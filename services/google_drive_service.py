import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv

load_dotenv()

class GoogleDriveService:
    def __init__(self, service_account_file='gcpkyawzin.ccna.json'):
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=self.scopes
        )
        self.service = build('drive', 'v3', credentials=self.creds)

    def list_files_in_folder(self, folder_id):
        """Lists files in a specific Google Drive folder."""
        results = self.service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(id, name, mimeType, createdTime)"
        ).execute()
        return results.get('files', [])

    def download_file(self, file_id, destination_path):
        """Downloads a file from Google Drive."""
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        with open(destination_path, 'wb') as f:
            f.write(fh.getvalue())
        return destination_path

    def move_file(self, file_id, source_folder_id, destination_folder_id):
        """Moves a file from one folder to another."""
        # Retrieve the existing parents to remove
        file = self.service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))
        
        # Move the file to the new folder
        file = self.service.files().update(
            fileId=file_id,
            addParents=destination_folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        return file

    def get_folder_id_by_name(self, folder_name, parent_id=None):
        """Finds a folder ID by its name."""
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.service.files().list(
            q=query,
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])
        return files[0]['id'] if files else None

    def create_folder(self, folder_name, parent_id=None):
        """Creates a new folder in Google Drive."""
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        file = self.service.files().create(body=file_metadata, fields='id').execute()
        return file.get('id')

    def share_folder(self, folder_id, email, role='writer'):
        """Shares a folder with a specific email address."""
        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }
        return self.service.permissions().create(
            fileId=folder_id,
            body=permission,
            fields='id'
        ).execute()

if __name__ == "__main__":
    # Test connection
    drive = GoogleDriveService()
    print("Google Drive Service initialized successfully.")
    # Here you could add more test logic if you have folder IDs
