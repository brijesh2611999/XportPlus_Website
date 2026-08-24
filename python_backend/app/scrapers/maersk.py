import subprocess
import json
import logging
import re

logger = logging.getLogger(__name__)

class MaerskScraper:
    def __init__(self):
        # We use the exact headers provided by the user that work in Postman/Curl
        self.headers = [
            "-H", "accept: application/json",
            "-H", "accept-language: en-US,en;q=0.9,hi;q=0.8",
            "-H", "akamai-bm-telemetry: a=D4FB9C8241910158BEAF93A7C7656778&&&e=MDg4QzU4NjMzNkYzNzk1OEFCNUJFOEM5OUMxRDcyMDd+WUFBUWZhTGZyVmdHSi95ZkFRQUFGSDRCSlFEa3RUZE1Id0NXRTdtUndQdlM1dFp4OUswMGtyR3V3VGIzRTJ5S3pjekxBdkhDU1AzaGtjd3BmVno0ZC9ZcEtXR2orM1VqZzJNRjQ3UzNEbk1RengyYW93UFBhdTBZaGp4WjVrYmw4M1NuODBXL0k0RXpwOVcyTnpvL3ZxdGw4R0ZmZ0g2SXI1WGwxTFZLelF4cmRDWXpjTHU4b2FTYWk4alUxbGdqTnkvbGpPeVN5aVFIOFN5bWRtelcwRkZObjZjOExxNk1KWEw0a2NlSHJwWVVBbTRyOGRXV0RvdDZjbGtxWlJZempvODc1OTFyZXRBQmsxLytVaEFkR1BqWTRtenNpRnBseHY2QmtUOG1CMFNySzJETzlvQlBmQW5WY3NBRnQ1UmF1UER4NU4ydjN3TUtlVVdsZ3FLTWkyOG50U21vbjFMd1V3Y3lUYTJuQy9ObzhqdzBodHVwNzFUa3Y4c0lUYnc4cnYxaHhiMzgwL1JoMkQvSVU3Yjl3R3dkeVJwblRycW1NVjVEUjJ4VFhxSDRqbDQwVFR1eX4zNjg3OTg2fjMxNjMxODU=&&&sensor_data=MjszNjg3OTg2OzMxNjMxODU7MTUsMiwwLDAsNCw0Mztjb0RpaU9hYHkpQEBOSTtuNDVVd1Mzbm9ZZ1tkSDtZLnRCJFRaPFddei5FWWRVWDJqeipSM3xnbGNxZnJNTXdaaXJFNi0uSk99eT5deWpqYmNsLWNhWk5dR1pecFpXL3FxMHhTZmN9NF9zP052dSNlS1pySSUrfjU7SEZaR1c1eTVIN3UofEpoPFUoQ2lqc2ZMcH13VVZNYkNoZ31NP35vN1Y/KXQ2Rm1yIFUpQ15bNihGOHhTbGsqNllmfik6dG8mRnk1VV83UCNHYyZrRFE5MmAtJHhxdktPICxVWmVXQHpDOS9RbTpeRnNRe0xkYncqWnxuZ357UGkzRnN4MTAqVn17ekdXQmpWNGA1czlgT1AqYGVTbiROaTxbM0deTFcgXlduUmdReUEgLS5xKVp9JmM+RT5hZURrRFc6T3Btb0svNjVuLSFITnx5S0ZeLDVPMGNzdTdFJVIyTzUteXwrZVRgdDZnVz8wbWRLOFpARlpEKTlAbntlN3NANFd6ITR8b3whZTd5ZklVVD0jXUFPalI5SWE0Sz5nSzFxOHV9NXpuKjR9Jk00QC8wdXVEN09lWUlbfk10VT4jXj98RmMzcGYrPDBxbF9lSlVGT35tMlVQNmF6Yi9wTk58ckwwU3ZfUn49Mm9vdXxtIH5wYlBsLTBwUHZVNCBfYEU5elRzPD88djZ7RXFUV1hwM0UtJEpzdlM9X0AmfG1vUVcqfEd2I3lIdHFaZ2wpPE9OVEE/ZEhCSyhLOXV+eGlfY0s/VHx7fH5RSDhOWH0gPHpiSVgjZWx8Si1rVF5WXVdfTj5iRlRkPyp6bzZGYXI6Q2ZVXS17KDtxUT86OjtXSEhESG9TZW9gP001Z25AUCYuXUpTQiotTy9scF9zdTIjOS0xZE5uJmpPXVYkMXcsX2pEP1QzKEleRHosb0Q/V2V+Y3dYSlkhbldhdTVTMlIySXl5JSN2OklHKjkrTU19IEhDWjkxTXJnV21xOEYrSChgUSk9Pi51OEpafG81RSxAbm56amYmVEw7I0AjSDVXXStnJD40N10rfXIyQlZvQ1V+Ljg3Jl8rZyokYklyLi15dnk1YV1iMV5lVnJ3I3lEYS5KKixdMjAxPC9KLyp9X0hPUk14eCRWMzkxWDUxXWgtM0IyY2xEWCsxVSpqNjBwaDh6SSM0OGRVVmQkQno9IEJ8NGBndlAtSlojVz91bFNVLyRDeSM7fmNzfUViR3VZJWEkWGNsVTtOaj5zYEk0KSZsUzN6IDJ+aisxaH5seCpbRmowTFRXN1JrViZ3XmZQZE5EZF5pOG9eezFvOzFiUTRsOm5dRTosRmRMKyBzJW18YnBOO1Zpa1tzN2o8OXFlRi1gRGF7dHQ/VEF8eyUvMigpKnFfKko3PV99bzguZm1MWHVuMlJOSX09MG4gaSwsPjpJNn1FdHd7Q11DKyR0blhTKSBIeW1sQWtzWWpieyhHO0RDMmo6Qzt8NThnbC9fTVU7KUd9NTt3Q0EzSUFgczw5QDw6cFBgYTFjWURROE5CRjMrWSxBVyhhYGF2d05kKCQ7NUIgTGRVUi4pbyh8Mnc6I3BJJjxTPCh3eT5HbGdJYCojPnRYZXs7M0o6OkRVVnhhZDZ4L1o7fi0pVGM9Yy47ZWRtVT1ncGF1Q0dXYCB1MjE1fWEqSDh3MzZefkVrR2o/RFIyJk9tXTVIVm9wPT1bTmlIQVV6eGkjMk5fNy9YfVZlfXNbWSxULjVAaXdLUnJ8NXVkP2VfUWl4WipnKWE/cSVFODFfLXt6JjlpcjpXdSs7NiVmICkwTl0yZkghazp6LlVNUCRaS1BwfEZjbkt3MFNCQHxWWEYpQF81JERib117OGpVKldMITFRe0ckJlJvJEpSKHN1eEpJKWpJYSNIR2o1bnlKMDdCbX1Mcld3anJGPEsta34oUCtRSkctLlVSeVNbb1Y3RlR0M3NBKVk8U3wkOiBrJTFpNDR1a1VfOHteK0loU0BDVSZVQGRZeGYoZG8kbFdxMUE5NHwvc3leUzZtI0JAIUFUK1FKdmQ4MV40OmRFRGd4Yzk8LSkoKCt+VTlkc29rMUghWDN4aFhAY05oKXp6QVhPLzUrMyl4NTZ5Wn1DT0VwLV46NSNoT1Epbn1FPU5xMX1pbnd4IHkpOSN4PG92ZkFYSH14XmtbTH1qNV1mZjdZV09TVm9xJC53KXpPISsuWDIjYVhKQTxBdnI9cHN2Uy0jejQyTFRzKy8wNmNFQUV1SUAhJnkzLC8gc0l2eDBtRjowTVd9M1dFam1jbEBHbloxaXg1cj1leVE1TWsqMXR5T0twLF1gOVIqbCF0OXIpUkRrNDxkOTY+RkFKdmI3JF59KEJLcXh8VDM5Sn12MmxXQUBmL2BOZGdwJmc8P3osbW4scG1GQFdZTXxkSFItRnwrQm1BKypPMGZHJCMqSGpyWSBNMTM3L2FaaTVLNHR9XVZSJktALVcuME5bZ1p+USAhTTkxQ14qVEM8b3MwaXhPQGFkfnNuS3F5aHUwLW5TM08xdzxuTixKNzxrb2pdeWxtaGV3YUQ5PUleV0RRNHN7ej1+WDlMbXY5UFcrUUFncjNRPzF6aWRpeUIpZXJufFF6empxZ15EO1VbbmcgIGY3b0Z1WS4pM21eT0E5LnJtNUEzO1NJL2dOcEV4Wi1ZLTg3KHxqK1VOZFpkNTNXJjxZZnNLTF0xUWxZWy87emlFNk1FOEMqeyQzXT1mSnF2KUx4LGolZDl3QnhtJSN6RlZMOkElLDY7fW15alI5eG9EUklDJl5rYW9BazZefjUjO0FiNjZNW0BzPCM9M3F9NV9JbGdhZzI9W1VyPnwyV2BwditBJDg8QVsgMyMuaEt7O2MqJHxNOyhhaDp6e0ZdXzlnXTZIUGAjMzJbbF01VzAmSUNGTG4sMjpUWSEgWCYgcXtodDk3W1U7VDxaTSRxJG1DIzFCYUdlajE6ezw7PSpPSTM/PSkxMSgxaTx0TyhoNWZ+eEMkPXpALnB3L24+eHN8OGE+KSRQcC1FVGNPbWlBIyQ4RUt1LjZiYHFyKUdsemJCM1NQXj5tRWRua2w1MlMxcEI+dyFdcU0uVnQlSnU3Q0cxLE5dZSt4MmE8Ny8hb08gVCM1L2hbYz5WUFFFUHtuYGJVeyVARGtRfW9oeDcxdzggXVlWLTZ1VD5zbDYgVG0uWldldlQ7UE9ZNilQPUojcnR8M2FSbV8udEoxb0BXOFlqLnxnNWY0PyAkSzQgcXs2Uz56YFpiPnNEPjZOIHt8TmhSel91c3ZaK0ZvSjI5MmRdeVAsTTBfV05PSz06PVc9YWd+eno/eS9OLVYvcHsrT25SJSNYSCNpLmtgeEwrNDReaUtyRyVLay8zL3lScmpRblc4KHFnPj5gPDUsdFpkb1lxVWVQIGxuMD5VQnZLPHlFYH0lXV05NG03akcqbTZ+UnFfK3NEKlMkLlMwdzJDK1pMNT4xPnZvQFZ1VGxXTWk8Z00jcCUvW3NIZ1VLZSFtMzYjPncxfnpMPFkocWJ9MyA8MG9xOjlmPVUkdmQoTz4gfmR6eXx6a1pSaikzUkZsVnlGUExRZjhEQDBJfE90XU1TUGlkJnVyNkZGdm5uc18gc085KlY5fEJpeX54TVt0eC4oST01OGp1eTJ7Oj1mPX1gYVBiS0YqfUZtLH5dISh0KTlQYWx8NCskTHw0RXY9LTtQN1sheF1GfGFoclQpLH03S29vOUFgWF8wbn4maEYyejQwQC5IfXxQLE9SblpNYmxvPWk/QCV8JG11PFhXKCN1NTlCO0VFPHleJTZqWXBtL0p3MlZqQDZMLnIpUDRycWR0L0pCYlJZNyk4ZFI/RlhxMj56V0hAU1pQNld1Y0tRTGVpPUZXX2REOk0kaGJtI011UHpXa0VMX15OezwhayAuQV14JVViaVFKcDErKzVJK0gwXT5fLkVkWVV6UE1AWVJvNVVkREheREpgNzQvUmdXclcrbD99PVBKU35XWE1gajhTLEByI0A0KGI0REZnfV0uelJGdlBvOkI+cFFVVGUmW35HakpUeHZ7UShrM24ubkUydmQ1JUx8eCxnSE9JdSNffWQmaHBISFk9e34jXVdnSD8mLWNGUikpc0x6QkJjLW5+eEZ7SFtrI2VNVHFKI19PUSYqZVIuYnsyd193eltuWzJxUyhNJS1OK3U6RHdgUzc8fTV4bzJ+N1NGN1FVMlJIaHE3MU8pQGBAL1J8XiUuc3sjfW1rPzBDalZTXiFdOHVRVCR0Uio5WlVSdDwmZGBCYFNnT1k4d0ByZ2IgRypXSDElZV4vdjpXVk58RT12IHctIE02QS55PGlpbStVQyYkXmNDNnFlJEdUWihFQipGPFBLTzkpZ1AqXm5mMV1ILTh9eV1nSzhhOzlDciU6M0BMZXctO0gvQGhORVkxW0wsL3cwJTx3Zj1qfStoODs4RFZ3LlNhbWFtQSYgQ3xMQSw4LHU6RTY0WDpKYD99LHhKVnwqYFkgICRxQFh2USE4JjU5PF0uKXhUNUI1elNmWndoQGUoTH10MkM1c0N8ZmRtZUVmdVNFT3laNVY6eT8jRlctPyU0SnMrMSZIZ0I3RixLezpMY1pNOyVFbFY/XWIzUClPNVB5MEE+Jk9xY1hkczQtV3AoMzJ9e0JoY2ByKGZzXSlwOG18OTMoUSV8X3Z+TF8sQW10e3ZzOnNyZHo3bEN8WEZtQmN8dm1Ic3lwMChjfU9gPkJoVlYoVlReJVElUEd1XSpvMFhNYnFgZmohQm0vZyZSciwlO2c3SksoNSNSRiMhSEBTeilBcWNWXXE/dTsgQG8qVFBhLXYqOmUycVFDLSFbVHM+T2RWJDtKd3xdbXA2TzNrYXhlSldxSHhZPzMmKV5QN2RzeXFWX0dCQ1V8ZWx2PkEqNH5oK0F0UEMwI0h3aVk5dFJvLHVoe0hJMl5+WT1ncSY8OnRCVzpzfFRmVGBMQiVwe0I9L1BAP25hOyBmUnpncEEpIEFwSzs6Li0lPDE/dF5vPzI9Un1hOXphWDE7a09lYWhOKlRUP0VMV1lvZ3JIP2A7PDFgemI7PHomaGgzJEZ6dHJIbWxRX0tsSig2NyYqVCkhJkd5bElHMTohKmVPc0xaVzBWTUtdZXklSk5XTUUkTVtkPGVZRklFQzo5ekw+ICoraEhDREpZcjFXW3d0aj59Nz9tTzw6QjNDQj4uLGVAQF17cHQhP1NzLk5heXB7W0RgaUUrJHhYdS9mQys5blFmKGhDXUt3e2BOPFZ5eiB8YXg0eFVGS2dudSVwMD5vWnMxWF4hek9nNVQpSmtuZG1aKUYycHpzNjZIZSAqKWNTeDosfCpFPyxpJmEuWGp4a18wREQuMypdYCs4ZmZyYFFlNEJ+TE8wUX5ZNlk0UGJWTn5BSS1APmhhR1ogLn4sNmQjZmZyYi1eS3ZXI2JQeWpFYzEuWj1SKTVwIVhbem5rNm5zdjxXM2lJKXxGdzlqXWl8eip8QEB6LXMwZSE5PjV0UVNJI0olZSgvelFDZiU2PXVVXWF0Mng+eTptKV5VWjNtKi9nKXlOTCgtUEBxQVJjPSoyM111YXtqNXAgX1ltWC9IXTBSUikvbnFEPEdJYXBiQWJZNFA4XUMoaC9aYnttSGh0UTN6YGhKWDUzZlNjKW5VaCZVJGZFK2FWbkdVdGROfiRsSEk+RDc1IXdhOGFyeVt4OHY4K2hgOiNNOUx1Z1duNncuOVJlV2BRVS4wRWpgVHE8eFJHIX5lYTBuL0RJSG08IGBlZ3xuNXApbV4qUlJGcTlxV1BDNnpvU0BYOC0wWil2YGJuICxLN04sLlMlLzRaKkVTUTlDMjJrXytWWlk4al9hVWUjLFZFZ0VWI2xBS21CLjJae3c5Mm0sIF5OcmZQJn57SCEpTl9qVVJWX3BnUj9ed3lBc2RxVFAodilKKVFzbis4YShWUGlUeSV0ciQhdHlXaV5sVld8Q1slL015OGI/UGtBYCo/YWRiTipfU1ExOSE9OVtLM0tNI2lBKks2cDhJdkliNmA7RFY2PFdyX0VVYGNjc04rLCpoclF+VE1XWXUpPH00SFlwcjVSUHNgS1NUdCxPYHl8OHtgMFdNOVZ3RmJAdFZ6VWl4cHQ0bFBKV15aMl9YQUZdTUV1N0I2Um9Nbllda2dMUSl8Rl54cnchViFAdCQuYyB5dUVydHA4VzxuUjJ5S31JdnElTSl6IzpVL0Z4Lm95PjU7Zk5aV30/JDdHJntSMlB4LC5ySlBUeTNtMWYpZyw7QVEvZyB9SXpsRTR1YkAyWWgxTWVrfnRPZ0VqWmxbe0A+XTp5MT5zejdxQSooaSwsLjdVQSE5eDtffUAsLDswakBXcXxvJWxlXT9NYjJ1bG9+Y1JGLzx7JX04cC8xTUkjKT9jUz1WdFJwUmlWWVhKMVp9PyRBRWsuZUkwZzd4bFRxOHdyQlRIK35tfGh+dW9aO2chJH48Xy5sX0Q5JGo+IT1dU1l6TTVyI3UpIEIuQnNtMV9iTi9JN1lkTEksJFVFdjE5K3VxWD9KRXxBIXJNKS10bHFwNyV8ODx4Oiw9c154YF1hNmZkV2xkJCRFR1tYRntLYFQzaEk0NSo7JCx5akB1cyNfLDN8P0RldT1EVVNHOGV6JGg1KGh2eSRwdHBdQW8kMX1dWFdre0RXeiVJSSMwaiRgfEV+c014KCVjMV4zRy06KXBIeTNFfipXc2Y7PSM4KUpZPGIwRnhfKHdFQ1hgVzQkQHwwIDtrVmBAcHIzZ2RvRjFycXQgNktbd21yVU5xKSFqIShRflB8S289RGJVP2csdGNyaDlCa2c4PlAzLUtuaV55K1IlXiVpalp2ZHV6VG9vU2B6Mj9qJk1SaVlPdUdIOVl3VHxjNw==",
            "-H", "api-version: v2",
            "-H", "consumer-key: UtMm6JCDcGTnMGErNGvS2B98kt1Wl25H",
            "-H", "dnt: 1",
            "-H", "origin: https://www.maersk.com",
            "-H", "priority: u=1, i",
            "-H", "referer: https://www.maersk.com/",
            "-H", 'sec-ch-ua: "Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
            "-H", "sec-ch-ua-mobile: ?0",
            "-H", 'sec-ch-ua-platform: "Windows"',
            "-H", "sec-fetch-dest: empty",
            "-H", "sec-fetch-mode: cors",
            "-H", "sec-fetch-site: same-site",
            "-H", "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        ]

    def track(self, tracking_number: str) -> dict:
        """
        Track a container or B/L using the Maersk API via curl subprocess
        to avoid Akamai Bot Manager blocking python requests.
        """
        operator = "MAEU" # For MAERSK
        url = f"https://api.maersk.com/synergy/tracking/{tracking_number}?operator={operator}"
        
        curl_command = ["curl", "--url", url, "-s"] + self.headers
        
        try:
            logger.info(f"Executing curl command for Maersk tracking: {tracking_number}")
            result = subprocess.run(curl_command, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"Curl command failed with code {result.returncode}")
                return {"error": "Failed to fetch data from Maersk API", "details": result.stderr}
                
            response_text = result.stdout.strip()
            
            # Check if it was blocked by Akamai
            if "<TITLE>Access Denied</TITLE>" in response_text or "Access Denied" in response_text:
                return {"error": "Request blocked by Akamai Bot Manager"}
                
            if not response_text:
                return {"error": "Empty response from Maersk API"}
                
            try:
                data = json.loads(response_text)
                return data
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Maersk response as JSON: {response_text[:200]}")
                return {"error": "Invalid JSON response from Maersk API"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Request to Maersk API timed out"}
        except Exception as e:
            logger.error(f"Error executing curl for Maersk: {e}")
            return {"error": str(e)}

