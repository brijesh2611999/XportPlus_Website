import requests

url = "https://www.yangming.com/api/CargoTracking/GetTracking?paramTrackNo=YMJAW237351291&paramTrackPosition=SEARCH&paramRefNo="

headers = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    print("Status:", response.status_code)
    print(response.text[:1000])
except Exception as e:
    print(e)
