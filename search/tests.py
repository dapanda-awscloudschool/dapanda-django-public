import requests
import time

url = "https://awscloudschool.online/product/2"

def fetch_url():
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Success:", response.status_code)
        else:
            print("Failed:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Error:", e)

def main():
    while True:
        for _ in range(10):
            fetch_url()
        time.sleep(1)

if __name__ == "__main__":
    main()
