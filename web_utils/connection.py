import os
import os.path as osp
import io
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import toml

class GoogleDriveManager:
    
    def __init__(self, credentials_path):
        self.credentials_path = credentials_path
        self.credentials = self.load_credentials()
        self.service = self.get_service()

    def load_credentials(self):
        # Load credentials from secrets.toml
        secrets = st.secrets["google_secret"].to_dict()

        # Create Credentials object from service account info
        credentials = service_account.Credentials.from_service_account_info(secrets)
        return credentials

    def get_service(self):
        # Build and return a service object
        return build('drive', 'v3', credentials=self.credentials)

    def delete_file(self, file_name, gdrive_path):
        # Function to delete a file from Google Drive
        if gdrive_path:
            folder_names = osp.split(gdrive_path)
            parent_id = None

            for folder_name in folder_names:
                parent_id = self.get_folder_id(folder_name, parent_id)
                if parent_id is None:
                    print(f"Folder '{folder_name}' not found in path '{gdrive_path}'.")
                    return False
        else:
            # If gdrive_path is empty, it means the file is in the root directory
            parent_id = 'root'

        # Query for the file in the specific folder
        query = f"name = '{file_name}' and '{parent_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print(f"File '{file_name}' not found in folder '{gdrive_path}'.")
            return False

        # Get the file ID and delete the file
        file_id = items[0]['id']
        try:
            self.service.files().delete(fileId=file_id).execute()
            print(f"File '{file_name}' deleted successfully from folder '{gdrive_path}'.")
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def get_folder_id(self, name, parent_id=None):
        # Function to check if a folder exists and return its ID
        query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        
        if items:
            return items[0]['id']
        else:
            return None

    # Add other methods as needed for interacting with Google Drive
    def create_folder(self, name, parent_id=None):
        folder_id = self.get_folder_id(name, parent_id)
        if folder_id:
            print(f"Folder '{name}' already exists with ID: {folder_id}")
        else:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            print(f"Folder '{name}' created with ID: {folder.get('id')}")
            folder_id = folder.get('id')
        return folder_id

    # Updated function to upload a file to a specific folder
    def upload_file(self, local_path, gdrive_path=''):
        if not os.path.isfile(local_path):
            print(f"File '{local_path}' does not exist.")
            return

        file_name = os.path.basename(local_path)

        # Handle the case where gdrive_path is empty
        if gdrive_path == '':
            parent_id = 'root'
        else:
            folder_names = osp.split(gdrive_path)
            parent_id = 'root'
            for folder_name in folder_names:
                parent_id = self.create_folder(folder_name, parent_id)

        # Check if the file already exists in the folder
        query = f"name = '{file_name}' and '{parent_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name, parents)").execute()
        items = results.get('files', [])

        file_metadata = {
            'name': file_name
        }
        media = MediaFileUpload(local_path, resumable=True)

        if items:
            # File exists, update it
            file_id = items[0]['id']
            existing_parents = ",".join(items[0]['parents'])
            updated_file = self.service.files().update(
                fileId=file_id,
                body=file_metadata,
                media_body=media,
                addParents=parent_id,
                removeParents=existing_parents,
                fields='id, parents'
            ).execute()
            print(f"File '{file_name}' updated in '{gdrive_path}' with ID: {updated_file.get('id')}")
        else:
            # File does not exist, create it
            file_metadata['parents'] = [parent_id]
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            print(f"File '{file_name}' uploaded to '{gdrive_path}' with ID: {file.get('id')}")

    # Function to download a file from Google Drive
    def download_file(self, file_name, gdrive_path, local_save_path):
        

        if gdrive_path == '':
            parent_id = 'root'
        else:
            folder_names = osp.split(gdrive_path)

            parent_id = None
            for folder_name in folder_names:
                print(folder_name)
                parent_id = self.get_folder_id(folder_name, parent_id)
                if parent_id is None:
                    print(f"Folder '{folder_name}' not found.")
                    return False
        print('\n\n\n\n\n\n ', file_name, parent_id)
        query = f"name = '{file_name}' and '{parent_id}' in parents and trashed = false"
        print('Quering')
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        print('Query ok')
        items = results.get('files', [])

        if not items:
            print(f"File '{file_name}' not found in folder '{gdrive_path}'.")
            return False

        file_id = items[0]['id']

        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        # Save the downloaded content to local file
        with open(local_save_path, 'wb') as f:
            f.write(fh.getvalue())

        print(f"File '{file_name}' downloaded to '{local_save_path}'.")
        return True

    # List files in the Drive
    def list_files(self, size=10):
        results = self.service.files().list(
            pageSize=size, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            return None
        
        return items
    
    # Function to print absolute path of a file in Google Drive
    def print_file_absolute_path(self, file_id):

        # Recursive function to get folder path
        def get_folder_path(folder_id, folder_name):
            print(f"\n Name: {folder_name} folder_id: {folder_id}")
            folder = self.service.files().get(fileId=folder_id, fields='id, name, parents').execute()
            parents = folder.get('parents', [])

            if len(parents) == 0:
                return ''
            else:
                parent_id = parents[0]
                parent_path = get_folder_path(parent_id, folder_name=folder['name'])
                return parent_path + '/' + folder['name']

        try:
            # Get file metadata
            file = self.service.files().get(fileId=file_id, fields='id, name, parents').execute()

            # Get initial folder ID
            parent_id = file.get('parents', [])
            print(file)
            if parent_id:
                parent_id = parent_id[0]
            print(parent_id)
            # Get absolute path of the file
            file_absolute_path = get_folder_path(parent_id, file['name']) + '/' + file['name']
            print(f"Absolute path of file '{file['name']}': {file_absolute_path}")

        except Exception as e:
            print(f"An error occurred: {e}")

    def delete_folder_recursive(self, gdrive_path):
        folder_names = osp.split(gdrive_path)
        
        if len(folder_names) > 1:
            # Traverse through the folder structure to find the correct parent ID
            parent_id = 'root'
            for folder_name in folder_names:
                parent_id = self.get_folder_id(folder_name, parent_id)
                if parent_id is None:
                    print(f"Folder '{folder_name}' not found in path '{gdrive_path}'.")
                    return False
            folder_id = parent_id
        else:
            # The folder is in the root directory
            folder_id = self.get_folder_id(name=folder_names[0], parent_id='root')
            if folder_id is None:
                print(f"Folder '{folder_names[0]}' not found in root directory.")
                return False
        
        # Now we have the folder ID we want to delete
        return self.delete_folder_recursive_by_id(folder_id)

    def delete_folder_recursive_by_id(self, folder_id):
        try:
            # List all items (files and subfolders) within the folder
            results = self.service.files().list(q=f"'{folder_id}' in parents and trashed = false", fields="files(id, name, mimeType)").execute()
            items = results.get('files', [])

            # Delete each item (recursively for subfolders)
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursively delete subfolder
                    self.delete_folder_recursive_by_id(item['id'])
                else:
                    # Delete file
                    self.service.files().delete(fileId=item['id']).execute()
                    print(f"Deleted file: {item['name']}")

            # Delete the folder itself
            self.service.files().delete(fileId=folder_id).execute()
            print(f"Deleted folder with ID: {folder_id}")
            return True

        except Exception as e:
            print(f"An error occurred: {e}")
            return False
        try:
            # List all items (files and subfolders) within the folder
            results = self.service.files().list(q=f"'{folder_id}' in parents and trashed = false", fields="files(id, name, mimeType)").execute()
            items = results.get('files', [])

            # Delete each item (recursively for subfolders)
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursively delete subfolder
                    self.delete_folder_recursive_by_id(item['id'])
                else:
                    # Delete file
                    self.service.files().delete(fileId=item['id']).execute()
                    print(f"Deleted file: {item['name']}")

            # Delete the folder itself
            self.service.files().delete(fileId=folder_id).execute()
            print(f"Deleted folder with ID: {folder_id}")
            return True

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def list_drive_tree(self, parent_id='root', indent=0):
        def build_tree_string(parent_id, indent):
            query = f"'{parent_id}' in parents and trashed = false"
            results = self.service.files().list(q=query, fields="files(id, name, mimeType)").execute()
            items = results.get('files', [])

            tree_string = ''
            if not items:
                return tree_string
            
            for item in items:
                tree_string += ' ' * indent + '- ' + item['name'] + '\n'
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    tree_string += build_tree_string(item['id'], indent + 2)
            return tree_string
        
        tree_string = build_tree_string(parent_id, indent)
        return tree_string

    def list_folders_in_folder(self, gdrive_path):
    # Split the path to get individual folder names
        folder_names = osp.split(gdrive_path)
        parent_id = 'root'

        # Traverse through the folder structure to find the correct parent ID
        for folder_name in folder_names:
            parent_id = self.get_folder_id(folder_name, parent_id)
            if parent_id is None:
                print(f"Folder '{folder_name}' not found.")
                return []

        # Query for all folders within the specified folder
        query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        return folders


    def delete_item(self, item_name, gdrive_path):
        folder_names = osp.split(gdrive_path)
        parent_id = 'root'

        if gdrive_path:
            for folder_name in folder_names:
                parent_id = self.get_folder_id(folder_name, parent_id)
                if parent_id is None:
                    print(f"Folder '{folder_name}' not found in path '{gdrive_path}'.")
                    return False

        # Find the item by name
        query = f"name = '{item_name}' and '{parent_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        items = results.get('files', [])

        if not items:
            print(f"Item '{item_name}' not found in path '{gdrive_path}'.")
            return False

        # Check the MIME type and delete accordingly
        item = items[0]
        item_id = item['id']
        item_mime_type = item['mimeType']

        if item_mime_type == 'application/vnd.google-apps.folder':
            return self.delete_folder_recursive_by_id(item_id)
        else:
            try:
                self.service.files().delete(fileId=item_id).execute()
                print(f"Deleted file: {item_name}")
                return True
            except Exception as e:
                print(f"An error occurred: {e}")
                return False