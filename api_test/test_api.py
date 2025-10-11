import requests # 오류가 있으면 “pip install requests”
username = input('username: ')
password = input('password: ')

HOST= 'http://127.0.0.1:8000'
res= requests.post(HOST + '/api-token-auth/', 
json={'username':username,'password':password}
)

res.raise_for_status()
token= res.json()['token']
print(token) 



# 인증이 필요한 요청에 아래의 headers를 붙임
headers= {'Authorization': 'JWT '+ token, 'Accept': 'application/json'}

# Post Create
data= {
    'author': 1,
    'title': 'API_test by code',
    'text': 'API_test by code',
    'created_date': '2025-10-11T18:34:00+09:00',
    'published_date': '2025-10-11T18:34:00+09:00'
}
file= {'image': open(r"C:\Users\seois\OneDrive\바탕 화면\배경사진\320quilotoa-banner.jpg", 'rb')}
res= requests.post(HOST+ '/api_root/Post/', data=data, files=file, headers=headers)
print(res)
print(res.json())