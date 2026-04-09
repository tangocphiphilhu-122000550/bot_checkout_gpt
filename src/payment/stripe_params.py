"""
Stripe Anti-Bot Parameters Generator
Generates required anti-bot parameters for Stripe payment API

STRATEGY: Hybrid approach
- REUSE: Static params from successful logs (guid, muid, pxvid, px3, captcha tokens)
- GENERATE: Simple dynamic params (sid, pxcts, init_checksum)
- This approach balances speed and reliability without needing browser automation
"""

import uuid
import secrets
import string
from typing import Dict


class StripeParamsGenerator:
    """Generate anti-bot parameters for Stripe API"""
    
    # ✅ STATIC PARAMS - Can be reused (from api.txt successful payment)
    STATIC_PARAMS = {
        "version": "d50036e08e",  # STRIPE_JS_BUILD_SALT - hardcoded in Stripe JS
        "guid": "8619d3f8-b4c8-4de7-8b84-fa10019443589092f2",  # Device fingerprint
        "muid": "f6570575-372b-4de5-8a49-f0a652d5b454a97f0b",  # Machine unique ID
        "pxvid": "5725299d-1eb6-11f1-aaa1-e1415a27a4fb",  # PerimeterX visitor ID
    }
    
    # 🔴 COMPLEX PARAMS - Reuse from successful log (too complex to generate)
    COMPLEX_PARAMS = {
        # PerimeterX anti-bot token (very long, encrypted)
        "px3": "ae13855387cf04b7d2ae773be68fcf7483a5b1e241b362e5a4a8d9d9f187960b:vrt2jThbdoRUhDwrL69yuAZDvoDSURbAKqd4S/PNKfd684Mft4itOuvguleB/u2FIF+Fz5wKn1gCaRpiQIxATQ==:1000:XQcvHDW8aGFW8yZeylGSz8fRtZTpQ39mjJ2Z8bZAE2H3+GaGTjanmgDlD/vyCYFbyG+Uj/d5aUY12tHn6D839l9g/EuhdywmflSrIx94cVt3irG1CkF1cnMUr3jafYbbgeEgfrVJnUE1ZWaZs2Ey7S5Uh0xbmbEmZM0JCiczPXSWn0rUHku7Nregg2C/+1Ck5CZ8EYyJ1W3UnpTQK6s6jbnTKpu+uPbgQQLe3GnHGMTM550owK0ys/t6xwE0Rhos5Xtq0lXAuRQIFMzn/DRrq34CQeqVyi97N3frgygH4PbtwxXp/T9aU4pstgh4xRgPiB2GP6ZCKn8xmTYbm3iff1XlOaqtDnPLYBIJ54SvtEapZZjguzwyyEegcKKR/I1OU0adhYqzPE6xUxKKh0b3Wr+eTFRkEwmE/OMcRwVqvAg7PKArXYkvTt3gTRNlWg2cbM1aLZuEEFLF5e8cZq78EKyl8u2/9iJRzgw0zdbSIbKf5GNoPTP4SRGzD+5p303JUEFzpWUakUeEKtkw67D1vYfDaxIHhlCM/fEAApsHLhm16uYRxJkx7nZs/VlUqzo2",
        
        # hCaptcha passive token (JWT format)
        "passive_captcha_token": "P1_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwZCI6MCwiZXhwIjoxNzc1NzEzODU5LCJjZGF0YSI6InRUSllHQU9uRjFpNGw5VmRwYnlsVnVDdkdTVkZzNGt1bUZjTHZoNDM1VlExeU0zRTR6NDlTZzhQMGRpNS80MEpObk9DVE1EN1JKRVFXSDFOakYvYnk3SmhMQUQxY3VJbnMwMmtxeTJOdEhLVXBVWVBvYnVNbG5Qd2JjZm9QdDM0anVkVlpjQWx4TU1pRVdIa2p2NlpwRFFHcjRrTmViaEJaU1lsR2hocVBPTlQxZk9qenIxdGtaK050RThGaFhaT2ZFYUhNNmlza1pBSUhjMkdoU2RNMUpreDNOOW51Y0FPR1ExWkVsQTFmZ2JKcytpUlRiamdDMHliVjlyVGtlMTdRR3RyUU0zdm5WUEI4elBzaVNIaHE3cEM0aWdzM0pVRlZFU2FqSzJ4RFFqQUpQR1F1ODJxbzF6VHNLczYydlI5K0l5SjdQOWNlYzUvaUgrNGVsbnkzYmF2U2UrOFZRSFg5YjJadVo5cEFVd21DOXhZc3BUWHgyTlNFY1hIMWlxTW9nTGlJNE1vUWhtaG9xajQ5N0IxRFZYenhpRTZwdG01VFV0UXJRWWV1b2lWOE5waU9lZEZtWXRiVkE9PVBWcWVWSW1DN1VlNDBHNTYiLCJwYXNza2V5IjoiMXpyR3ZOamlHNERrRzREUFpGZW5adnBvYXZnR0xZOEJDTU82QjNadGFIYjgrOWgvdUgxNzVrTlFZNkgwZ2JKcEx6aXVycDQ4QjJNMStsbDVBN0NzeG5Rc0o5MUYzYk9TZ1ZJQzRvMFRzS2hzVkVNV1JSMGJuR2ZjNHAxVmx6N2N0RUhLbVZtWWtIclBHUE43Ry9SbElxZUZOcER3MlNlcjUzeFN0ekcxazNVdnc5V1JFSExJZlNIQmtlZkgrSk5qendGazNVMXVHWVR0VmpsVzNsUDIxK3Y3cUNyc25WNVZpUGhCa2pmQUsvZCt0NjJvVDIvNEhveG5ickdTQ3VSeWtPWjdzaVc2L0MxcE5BV3NYODM4c0I2UVZJS2s5Mk4zQ3ltV05iQTRSbnlOWENMWFpjRkpkNnBMdCtEa0plWll1VE5VOWMzUGR0ZFB4MnNXTzVUSFlteFcrZ3hvTG55N0pyOVVQdWEzYUErZDJVYjdvNnVZd2gwdGJSQ1c2Zk82eSt2ZVhlV2d3eHNMZzBmc3pCc21XUktkUlZHVENWenpiaURoaFJJNWREZHUxRW81NCt6TlY0c1AyNEtrSFZ3WWo1SE5Uc0ticHhzaThFN2ZXSmlXRmlWMnZrK2pDK0hnUTh1K0hjMXQwa0JVTnhOSnoxT1dUT2ZJWnJhVUJDTFNPN01Pdkx5TmN6VTRmbm1MVjVBdldUTkdIbUJoTVU4SThmbjErVmN5RTBuVEdmVHc4ZDdZdlRJRnlGa2Jad0NSdWI0bFVWdXhUc0kvUjFLc3JyaE9QaUpiNm4yY2V4T0tXbkpQbkNKUitWSmFhdUhkTzN0WFVtM2lvN2dsM1JtNm5WRWp1V2JacHplOHdzMUgzbEwxUHpVWHdtVjR3a1BXTmE3M3lpbHJ6RVZCeEtKbEswYXVUdFdOclpWOGxQY21MVjNGR2pKV0gzc3NWTzlOa0NsUy9DbTh6YU9rbVNndnczb2xlRVg1aHFBdUpVTU40UXVPbDdyVzVONndxNXB0RjNncGRNV0N3QUd5WldkOGR5Wm55NWVlaFc4TTFBa25tV1VPNlkrUis1K2QvUVNNSjBNU3dpMWYxaW5DaEVWb3lCWE5XczFMU1cwR2taczFiNnFvenEzVTBTbFNoaHpQcmlOQjRtaTlIRGtkeHBFRkxFRXl3Z0Y5Ui93MmgxZmVTcVZQQTFhdVJ4bHk5YnRnSm0zT1J3eDdyVWdEMmdwNVVjVUYybzVwZXFqS0RURmNER1BwRFVXTGtiWExkOTBDSUdIQ29KS3hlNkM2S29JdEdxanRwSmh5cEUvQUxQOGc3YktoaTNvME1Dd29LYk5QUHc1bjVYWTdSdlFsWEpEM0dIclF1R0IzSnl1QS9zbEVadHJrUWxSdHRUbm5icHJ5UnN2aE5rV29vUFh0NlMxeEQwNHc5b3BGcU52dnpxbDhQTmpxUkpueGtlNnBOZ0hsUEY1ckFTK2ozdnhrTDZmcENYdTM5SjV4K3JQQmkwdTZYVFgweHJHWlA1M08zSm5RQllWN3dRRzducGQvblBCNzVzMGY1UXpDVmp1NVM0QUM5Z29LMURyLy8xblIrM0gxRHZUdm5udENMdnZmZGY3Y3BMWVBzSVQxMEJ3Umh1VHFrdTBuT2RFbUVlbzlFaDM5TUJSTVhrTWprWWt6a2hHL1M4ZkxRS1NIMFhVNzN2MUt0MmVMOEZraVRMSGsxazErbU1qaEVVcmJ4OHZKMFB5VnZVWURZTW5ycnNOUnN3czZBakNIbjdxWWNLcWxvR2I2ckxqRUlQd2VFV3pRb2pabHJTMTBCRjI5RUxoVjVNdTFQejdzVVJTbmVjbnZzNHEvaUcvRFFOUDVoV0dPdVJ0UG5aajdBb2NlNXpVZEtBQ3krcGhmMnhaQ3BUdHJia3Vqa1NDTklWcjZiUGZoSW93ZGhQc2hORFJqNk1Pai9qNWhqV2JqckdxcEV4Q1lmUEQyK1JsSWV3UURJNFpHSDlFcXNBZXcvVGlCUVp0MTZhY2NUM2pKMXY5Zkc2TU1MYjlmQ2FRcmFQMUhxQTFtUnB4Tnk2SWdJK2xsQkFNU0FYNStFeGg5TlZmNTdROWhRYXBkYWg1OEIrdnRiQWZWVGx1KzkvU2pOcjhkUFFmcmhvZDFYY1g1Z3BicWZOUFcxdS9RMmZHTUNTV1Q1Kyt6YkZmRE9MaVFDazI1Z2hYK0NYOXpUWlhKbzJwNDNLZmNiVUcvRGU0eEc1OVhUWElVVzBWYWRKYjdhRFBvRnhPWEN6MWVZd2tqeXV0WnhEQkhUVXFnOTBoQi9iN2Q1emJ0MVNMY0E3TmNobFlJbWR4Q1p2ZlFsT3VtNlhNc3R5Tk9aWk1yT2swL2pwWTcrNVNOQ0FSSTR4Ynh0ZGNsUElGdmNFdTRBV3NtWFVCSjhvL3NoWmRycmxnSGhzVWZyYWtkOTVjNFhIblhyL3l5NDdVMGQwKy8wMS9KMVlXWitYbXFDTzZjVHZrWFMzbHUyYStFcDUwbC9lMEthbEswRUk3bFJ5Mno4YXdyZERsN0R3bVozNFAzbEc2bThEOW1Ta0NEaVM0U244RkFYZEhQeW5NRXBJOEhSSHJXV2JBZU1RNkRNcU9GWFUrRko1cFMrZkwrbnQrTDQxN3EzQTNEcXlwanJFNlp1Nm9GQTN3UUhQRGJhQkpiaXJsMVQrU2dEZGpDMVJGaG9BNlZhWUw0ZzNUVktIUFg4Sjk4NmhaUDZpOW1DZ3V5ZnBweE1SZHlNZWdwODB4YXhNcFd3Qk1obGR0bEFFZllYdHNINWFoQTYzUWw1SGFLd2Jjekc3NCtDODJ1Q2lKUUZUYVRrVVp0ZFNVQ0xkeVJwaVB3eURUbFZSSzg3Rzgva1JNc1U3VGJKMC8yUm9FNFhTdDZORFV1QUxQaGltWWtFdTFKV0x3UGNjWW9ITk11UFZKWjJlU2FZQ2tKWVZjWDFJeUR0a1FkUFhMMlFXSHp4VWhZQW9Zd3h2OG1zcmR2YTJIYWk1anUrdmRiSFlkSGR3PT0iLCJrciI6IjRhZTQ1YTJlIiwic2hhcmRfaWQiOjM2MjQwNjk5Nn0.ll5vOMfrlmRCdJKuIYFSrKhJdxL91ao9FGctfy17CWI",
        
        # Passive captcha ekey (empty in logs)
        "passive_captcha_ekey": "",
        
        # Radar timestamp (encrypted, same in both logs)
        "rv_timestamp": "qto>n<Q=U&CyY&`>X^r<YNr<YN`<Y_C<Y_C<Y^`zY_`<Y^n{U>o&U&Cyd_L<Y_d&dO`DdOavXuTCXOX<YOUsex\\<YOard=\\#X&PC[Rd>Y_T<Xtn{U>e&U&CyY=PDX&QyX&]rXuUxYxd#[OP%[R]sY&`$YbL;XRX#Y=eveRevXRn%[_\\;eRL<X&#=euereuP#eudCXRMu[_`Cd^o?U^`w",
        
        # JS checksum (56 chars, can be hardcoded)
        "js_checksum": "qto~d^n0=QU>azbu]]_>aLl`d&m_]}q`U|_Oesdw]!ox<^e%o?U^`w",
    }
    
    def __init__(self):
        pass
    
    def generate_sid(self) -> str:
        """Generate session ID (UUID + 6 random hex chars)"""
        base_uuid = str(uuid.uuid4())
        random_suffix = ''.join(secrets.choice(string.hexdigits.lower()) for _ in range(6))
        return f"{base_uuid}{random_suffix}"
    
    def generate_pxcts(self) -> str:
        """Generate PerimeterX timestamp (UUID format)"""
        return str(uuid.uuid4())
    
    def generate_init_checksum(self) -> str:
        """Generate init checksum (32 chars alphanumeric)"""
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(32))
    
    def get_all_params(self) -> Dict[str, str]:
        """
        Get all anti-bot parameters
        
        Returns:
            Dict with all required params for Stripe API
        """
        return {
            # Static params (reused)
            **self.STATIC_PARAMS,
            
            # Complex params (reused from successful log)
            **self.COMPLEX_PARAMS,
            
            # Dynamic params (generated)
            "sid": self.generate_sid(),
            "pxcts": self.generate_pxcts(),
            "init_checksum": self.generate_init_checksum(),
        }
