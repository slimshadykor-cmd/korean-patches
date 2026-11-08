from pathlib import Path
import hashlib, difflib

root = Path(__file__).resolve().parent
source = (root.parent / 'research/vk_dxgi.h').read_text()
blob = hashlib.sha1(b'blob ' + str(len(source.encode())).encode() + b'\0' + source.encode()).hexdigest()
assert blob == '0c53d23b0d755d9c9986f2c8ed65a91d70fe5705', blob
text = source
def replace(old, new):
    global text
    assert text.count(old) == 1, (old, text.count(old))
    text = text.replace(old, new)

# Windows SDK and MinGW headers disagree on this enum's underlying-type spelling.
# Include its canonical definition instead of forward-declaring a different type.
replace('enum D3D_FEATURE_LEVEL : int;', '#include <d3dcommon.h>')

replace('  DVK_OK,\n', '  DVK_NOT_READY = -1,\n  DVK_OK = 0,\n')
replace('dvk_presentationInfo_t * pPresentationInfo ) noexcept;',
        'dvk_presentationInfo_t * pPresentationInfo, DWORD timeoutMs = 1000 ) noexcept;')
replace('dvk_presentationInfo_t * pPresentationInfo ) noexcept\n{',
        'dvk_presentationInfo_t * pPresentationInfo, DWORD timeoutMs ) noexcept\n{')
replace('WaitForSingleObjectEx( pSwapChain->presentationWaitHandle, 1000, true )',
        'WaitForSingleObjectEx( pSwapChain->presentationWaitHandle, timeoutMs, false )')
replace('return dvk_result_t{ .code = DVK_ERROR, .message = DVK_PREPEND( "Timeout while waiting for the presentation event" ) };',
        'return dvk_result_t{ .code = DVK_NOT_READY, .message = DVK_PREPEND( "Presentation event is not ready" ) };')
replace('  HRESULT result = parameters.pDeviceContext->pDxgiFactory->CreateSwapChainForHwnd(\n    parameters.pDeviceContext->pCommandQueue, parameters.window, &swapChainDesc, NULL, NULL, (IDXGISwapChain1 **)&pSwapChain->pSwapChain );',
'''  IDXGISwapChain1 * baseSwapChain = nullptr;
  HRESULT result = parameters.pDeviceContext->pDxgiFactory->CreateSwapChainForHwnd(
    parameters.pDeviceContext->pCommandQueue, parameters.window, &swapChainDesc, NULL, NULL, &baseSwapChain );
  if ( SUCCEEDED( result ) )
  {
    result = baseSwapChain->QueryInterface( IID_PPV_ARGS( &pSwapChain->pSwapChain ) );
    baseSwapChain->Release();
  }''')
replace('pSharedImage->pVkImage != nullptr && pSharedImage->pVkImage != VK_NULL_HANDLE',
        'pSharedImage->pVkImage != nullptr && *pSharedImage->pVkImage != VK_NULL_HANDLE')
from ring_copy import apply_ring
text = apply_ring(text)
(root/'vendor').mkdir(exist_ok=True)
(root/'vendor/vk_dxgi.h').write_text(text)
(root/'vendor/LICENSE').write_bytes((root.parent/'research/vk_dxgi.LICENSE').read_bytes())
(root/'vendor/local-changes.patch').write_text(''.join(difflib.unified_diff(
    source.splitlines(True),text.splitlines(True),fromfile='upstream/vk_dxgi.h',tofile='vendor/vk_dxgi.h')))
print('Verified upstream and applied bounded-wait / COM interface / cleanup changes.')
