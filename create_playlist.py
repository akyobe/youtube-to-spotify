import json 
import os 
import google_auth_oauthlib.flow 
import googleapiclient.discovery
import requests
import youtube_dl
import googleapiclient.errors 

from secret import spotify_token, spotify_user_id

class CreatePlaylist: 
    def __init__(self): 
        self.youtube_client= self.get_youtube_client()
        self.all_song_info = {}
        
  
    #log into YOUTBE 
    def get_youtube_client(self):
        # FROM YOUTUBE DATA API WEBSITE 
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"]="1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json" 
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file,scopes
        )
        credentials = flow.run_console()

        youtube_client= googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials
        
        )
        return youtube_client 

  
    # Grab your liked Videos
    def get_liked_videos(self): 
        #FROM YOUTUBE Data API 
        requests = self.get_youtube_client().videos().list( 
            part ="snippet,contentDetails,statistics",
            myRating="like"
        )
        response = requests.execute()


        #Collections information from each video and stroes it 
        for item in response ["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])
        #Use Youtube DL Library to extract information from the video
            videos = youtube_dl.YoutubeDL({}).extract_info(
                youtube_url, download=False
            )
            song_info = videos["title"].split("-")
            artist= song_info[0]
            song_name = song_info[1]

            #If the song information passed correctly, add it  to our dictionary
            if song_name is not None and artist is not None: 
                uri =self.get_spotfiy_uri(song_name, artist)
                if(uri !=""):
                    self.all_song_info[video_title]={
                        "youtube_url": youtube_url, 
                        "song_name": song_name,
                        "artist": artist, 
                        "spotifiy_uri": uri
                    }
  
    #Creates a New Playlist
    def create_playlist(self):
        request_body = json.dumps({
            "name": "Youtube Liked Videos",
            "description":"This playlist is created from your liked videos on Youtube!",
            "public": True
        })
        query = "https://api.spotify.com/v1/users/{}/playlists".format(spotify_user_id) 
        response = requests.post(
            query, 
            data = request_body, 
            headers ={
                "Content-Type": "application/json", 
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        #print out the contents of the response
        response_json = response.json()

        #playlist id
        return response_json["id"]

        pass 

    #Search for song in Spotify 
    def get_spotfiy_uri(self, song_name, artist): 
        query= "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        ) 
        response_json = response.json()
        song = response_json["tracks"]["items"]
        if(len(song)>0):
            uri = song[0]["uri"]
        else: 
            print("Unable to download {} by {}".format(song_name,artist))
            return ""

        return uri
  
    #Add Song to playlist 
    def add_song_to_playlist(self): 
        #populate our songs dictionary 
        self.get_liked_videos()

        #collected all of uri 
        uris = [info["spotify_uri"] for songs , info in self.all_song_info.items()]

        playlist_id = self.create_platlist()
        request_data = json.dumps(uris)

        query ="https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers= {
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )

        response_json = response.json()
        return response_json


if __name__ == '__main__': 
    cp = CreatePlaylist()
    cp.add_song_to_playlist() 

