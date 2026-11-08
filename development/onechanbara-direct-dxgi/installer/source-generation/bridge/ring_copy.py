"""Transform the pinned interop helper to independent shared images/timelines."""
def apply_ring(text):
    def replace(old, new):
        nonlocal text
        assert text.count(old) == 1, (old[:100], text.count(old))
        text = text.replace(old, new)

    replace('  dvk_sharedImage_t        sharedImage       = {};',
            '  dvk_sharedImage_t        sharedImage       = {};\n'
            '  VkImage                  vkBlitImage       = VK_NULL_HANDLE;\n'
            '  dvk_sharedImage_t        blitImage         = {};')
    replace('  VkImage           vkBlitImage = VK_NULL_HANDLE;\n  dvk_sharedImage_t pBlitImage  = {};\n', '')
    replace('  uint64_t      fenceValue        = 0;',
            '  uint64_t      fenceValue        = 0;\n'
            '  // One producer per timeline: Vulkan renders, D3D12 copies.\n'
            '  ID3D12Fence * pCopyFence = nullptr;\n'
            '  HANDLE copyFenceSharedHandle = INVALID_HANDLE_VALUE;\n'
            '  VkSemaphore copySemaphore = VK_NULL_HANDLE;')
    # Both the acquired token and present parameters carry the copy timeline.
    needle='ID3D12Fence *'
    for struct_name in ['dvk_presentationInfo_t', 'dvk_presentParameters_t']:
        start=text.index('typedef struct '+struct_name)
        end=text.index('} '+struct_name+';',start)
        block=text[start:end]
        lines=block.splitlines(True)
        line=next(s for s in lines if needle in s)
        replace(block, block.replace(line,line+'  ID3D12Fence * pCopyFence = nullptr;\n'))

    # Create a second imported timeline, preserving failure cleanup at each step.
    a=text.index('  result = parameters.pDeviceContext->pD3D12Device->CreateFence( 0,')
    b=text.index('  return dvk_result_t{ .code = DVK_OK };\n}',a)
    block=text[a:b]
    copy=block.replace('pSwapChain->pFence','pSwapChain->pCopyFence')\
              .replace('pSwapChain->fenceSharedHandle','pSwapChain->copyFenceSharedHandle')\
              .replace('pSwapChain->semaphore','pSwapChain->copySemaphore')
    text=text[:b]+'''  if ( __dvk_hasSwapChainFlag( pSwapChain->flags, DVK_SWAPCHAIN_BACKBUFFER_BLIT_FLAG ) )
  {
'''+copy+'''  }

'''+text[b:]
    replace('  if ( pSwapChain->semaphore != VK_NULL_HANDLE )\n',
'''  if ( pSwapChain->copySemaphore != VK_NULL_HANDLE )
  {
    pSwapChain->pFunctions->vkDestroySemaphore( pSwapChain->pVulkanContext->device, pSwapChain->copySemaphore, nullptr );
    pSwapChain->copySemaphore = VK_NULL_HANDLE;
  }
  if ( pSwapChain->copyFenceSharedHandle != INVALID_HANDLE_VALUE )
  {
    CloseHandle( pSwapChain->copyFenceSharedHandle );
    pSwapChain->copyFenceSharedHandle = INVALID_HANDLE_VALUE;
  }
  if ( pSwapChain->pCopyFence != nullptr )
  {
    pSwapChain->pCopyFence->Release();
    pSwapChain->pCopyFence = nullptr;
  }
  if ( pSwapChain->semaphore != VK_NULL_HANDLE )
''')
    # The command allocator is reused only after this slot's D3D12 copy ended.
    replace('pSwapChain->pFence->GetCompletedValue() < pFrameResources->lastBlitValue',
            'pSwapChain->pCopyFence->GetCompletedValue() < pFrameResources->lastBlitValue')
    replace('pSwapChain->pFence->SetEventOnCompletion( pFrameResources->lastBlitValue, nullptr )',
            'pSwapChain->pCopyFence->SetEventOnCompletion( pFrameResources->lastBlitValue, nullptr )')
    replace('src.pResource = pSwapChain->pBlitImage.pImage;',
            'src.pResource = pFrameResources->blitImage.pImage;')
    replace('''    // When bliting the image to the backbuffer the synchronization is sequential, waiting on the single blit buffer
    waitFenceValue   = pSwapChain->fenceValue;
    submitFenceValue = ++pSwapChain->fenceValue;
    blitFenceValue   = ++pSwapChain->fenceValue;''',
'''    // Reuse only this slot's image. Other slots may render while D3D12 copies.
    // Equal values on TWO distinct timelines cannot signal each other early.
    waitFenceValue   = pFrameResources->lastBlitValue;
    submitFenceValue = ++pSwapChain->fenceValue;
    blitFenceValue   = submitFenceValue;''')
    replace('                                               .pFence          = pSwapChain->pFence,',
            '                                               .pFence          = pSwapChain->pFence,\n'
            '                                               .pCopyFence      = pSwapChain->pCopyFence,')
    replace('.waitSemaphore   = pSwapChain->semaphore,',
            '.waitSemaphore   = pSwapChain->pCopyFence ? pSwapChain->copySemaphore : pSwapChain->semaphore,')
    replace('presentParameters.pCommandQueue->Signal( presentParameters.pFence, presentParameters.blitValue )',
            'presentParameters.pCommandQueue->Signal( presentParameters.pCopyFence, presentParameters.blitValue )')

    a=text.index('  // Create the blit image used for rendering and copy to the swapchain')
    b=text.index('  for ( size_t idx = 0; idx < swapChainImageCount; ++idx )',a)
    block=text[a:b]
    replace(block,block.replace('if ( __dvk_hasSwapChainFlag( pSwapChain->flags, DVK_SWAPCHAIN_BACKBUFFER_BLIT_FLAG ) )',
        'for ( size_t slot = 0; slot < swapChainImageCount && __dvk_hasSwapChainFlag( pSwapChain->flags, DVK_SWAPCHAIN_BACKBUFFER_BLIT_FLAG ); ++slot )')
        .replace('pSwapChain->pBlitImage','pSwapChain->pPerFrameResources[slot].blitImage')
        .replace('pSwapChain->vkBlitImage','pSwapChain->pPerFrameResources[slot].vkBlitImage'))
    replace('pSwapChain->pExternalSwapChainImages[idx] = pSwapChain->vkBlitImage;',
            'pSwapChain->pExternalSwapChainImages[idx] = pPerFrameResources->vkBlitImage;')
    replace('      __dvk_destroySharedImage( pSwapChain, &pImportedSwapChainImage->sharedImage );',
            '      __dvk_destroySharedImage( pSwapChain, &pImportedSwapChainImage->sharedImage );\n'
            '      __dvk_destroySharedImage( pSwapChain, &pImportedSwapChainImage->blitImage );')
    replace('  __dvk_destroySharedImage( pSwapChain, &pSwapChain->pBlitImage );\n', '')
    # Drain the copy queue on teardown. Do not signal the Vulkan-owned timeline.
    a=text.index('static dvk_result_t __dvk_waitIdle( dvk_dxgiSwapChain_t * pSwapChain ) noexcept\n{')
    block=text[a:]
    block=block.replace('  HRESULT result = pSwapChain->pDeviceContext->pCommandQueue->Signal( pSwapChain->pFence, ++pSwapChain->fenceValue );',
        '  ID3D12Fence * drainFence = pSwapChain->pCopyFence ? pSwapChain->pCopyFence : pSwapChain->pFence;\n'
        '  HRESULT result = pSwapChain->pDeviceContext->pCommandQueue->Signal( drainFence, ++pSwapChain->fenceValue );')\
        .replace('pSwapChain->pFence->GetCompletedValue()', 'drainFence->GetCompletedValue()')\
        .replace('pSwapChain->pFence->SetEventOnCompletion(', 'drainFence->SetEventOnCompletion(')
    text=text[:a]+block
    return text
