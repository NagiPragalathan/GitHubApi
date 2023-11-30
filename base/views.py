from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_jwt.settings import api_settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render


def welcome(request):
    BASE_PATH = request.build_absolute_uri('/')
    return render(request,'welcome.html',{'base_url':BASE_PATH})

@api_view(['POST'])
def user_registration(request):
    if request.method == 'POST':
        obj = User(username=request.data['username'],password=make_password(request.data['password']),email=request.data['email'])
        obj.save()
        if obj:
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response({'Error occurd while creating user..!'}, status=status.HTTP_400_BAD_REQUEST)

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    print(request,request.user)
    if request.method == 'POST':
        logout(request)
        return Response({'message': 'Logout successful'})
    return Response({'message': 'User not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests

def get_github_profile_data(username):
    def fetch_data(api_endpoint):
        url = f'http://github-profile-summary-cards.vercel.app/api/cards/{api_endpoint}?username={username}&theme=default'
        response = requests.get(url)

        if response.status_code == 200:
            return response.text
        else:
            print(f"Error: Unable to fetch {api_endpoint}. Status code: {response.status_code}")

    svg_data = {"profile_data" :fetch_data('profile-details'),
    "repos_language":fetch_data('repos-per-language'),
    "most_commit_language":fetch_data('most-commit-language'),
    "stats":fetch_data('stats'),
    "productive_time":fetch_data('productive-time')}
    return svg_data

from django.http import HttpResponse

def svg_server(request, data, username):
    def fetch_data(api_endpoint):
        url = f'http://github-profile-summary-cards.vercel.app/api/cards/{api_endpoint}?username={username}&theme=default'
        response = requests.get(url)

        if response.status_code == 200:
            return response.text
        else:
            print(f"Error: Unable to fetch {api_endpoint}. Status code: {response.status_code}")
            return None

    if data == "profile_data":
        svg_data = fetch_data('profile-details')
    elif data == "repos_language":
        svg_data = fetch_data('repos-per-language')
    elif data == "most_commit_language":
        svg_data = fetch_data('most-commit-language')
    elif data == "stats":
        svg_data = fetch_data('stats')
    elif data == "productive_time":
        svg_data = fetch_data('productive-time')
    else:
        return HttpResponse("Invalid data parameter", status=status.HTTP_400_BAD_REQUEST)
    if svg_data:
        return HttpResponse(svg_data, content_type='image/svg+xml', status=status.HTTP_200_OK)
    else:
        return HttpResponse("Failed to fetch SVG data", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
import requests
from bs4 import BeautifulSoup

def get_github_profile_stats(username):
    # GitHub profile summary cards API endpoint
    url = f'https://github-profile-summary-cards.vercel.app/api/cards/stats?username={username}&theme=default'

    # Make a GET request to the GitHub profile summary cards API
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML response with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text elements within the SVG
        text_elements = soup.find_all('text')
        start = False
        keys_ = []
        values_ = []
        output = {}

        # Extract text content
        for text_element in text_elements:
            if start:
                isnum = text_element.get_text(strip=True).isalnum()
                if isnum:
                    keys_.append(text_element.get_text(strip=True))
                else:
                    values_.append("_".join(text_element.get_text(strip=True).split(" ")))
            start = True

        # Create a dictionary with key-value pairs
        output = {value: key for key, value in zip(keys_, values_)}

        return output

    else:
        # Return None if the request was not successful
        print(f"Error: Unable to fetch data. Status code: {response.status_code}")
        return None
    



@api_view(['GET'])
def github_user_info(request, username):
    base_url = f"https://api.github.com/users/{username}"
    events_url = f"https://api.github.com/users/{username}/events/public"
    BASE_PATH = request.build_absolute_uri('/')
    
    try:
        # Make a GET request to the GitHub API for the user
        user_response = requests.get(base_url)
        user_response.raise_for_status()  # Raise an exception if there's an HTTP error
        
        events_response = requests.get(events_url)
        events_response.raise_for_status()  # Raise an exception if there's an HTTP error
        
        user_data = user_response.json()
        events_data = events_response.json()
        
        # Calculate total contributions
        no_of_stars = sum(1 for event in events_data if event.get("type") == "PushEvent")
        svg_data = get_github_profile_data(username)
        links = [f"{BASE_PATH}svg_server/{i}/{username}" for i in svg_data.keys()]
        
        profile = get_github_profile_stats(username)
        user_data.update(profile)
        user_data["no_of_stars"] = no_of_stars
        user_data["links"] = links
        user_data["svg_data"] = svg_data
        response_data = user_data

        return Response(response_data, status=status.HTTP_200_OK)
    
    except requests.exceptions.RequestException as e:
        return Response({"error": f"Error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
