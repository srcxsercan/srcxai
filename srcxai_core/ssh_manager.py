"""
SSH Remote Editing Module
Handles SSH connections and remote file editing capabilities
"""

import paramiko
import os
import stat
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import tempfile


class SSHManager:
    """Manages SSH connections and remote operations"""
    
    def __init__(self):
        self.connections: Dict[str, paramiko.SSHClient] = {}
        self.sftp_clients: Dict[str, paramiko.SFTPClient] = {}
    
    def connect(self, host: str, username: str, port: int = 22,
                password: Optional[str] = None, key_path: Optional[str] = None,
                alias: Optional[str] = None) -> bool:
        """Establish SSH connection"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if key_path:
                key = paramiko.RSAKey.from_private_key_file(key_path)
                client.connect(host, port=port, username=username, pkey=key)
            elif password:
                client.connect(host, port=port, username=username, password=password)
            else:
                # Try to use SSH agent
                client.connect(host, port=port, username=username)
            
            connection_id = alias or f"{username}@{host}:{port}"
            self.connections[connection_id] = client
            
            # Create SFTP client
            sftp = client.open_sftp()
            self.sftp_clients[connection_id] = sftp
            
            return True
        except Exception as e:
            print(f"SSH connection failed: {e}")
            return False
    
    def disconnect(self, connection_id: str):
        """Close SSH connection"""
        if connection_id in self.sftp_clients:
            self.sftp_clients[connection_id].close()
            del self.sftp_clients[connection_id]
        
        if connection_id in self.connections:
            self.connections[connection_id].close()
            del self.connections[connection_id]
    
    def disconnect_all(self):
        """Close all SSH connections"""
        for connection_id in list(self.connections.keys()):
            self.disconnect(connection_id)
    
    def execute_command(self, connection_id: str, command: str) -> Tuple[str, str, int]:
        """Execute command on remote system"""
        if connection_id not in self.connections:
            raise ValueError(f"No connection found for {connection_id}")
        
        client = self.connections[connection_id]
        stdin, stdout, stderr = client.exec_command(command)
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        
        return output, error, exit_code
    
    def read_remote_file(self, connection_id: str, remote_path: str) -> str:
        """Read file from remote system"""
        if connection_id not in self.sftp_clients:
            raise ValueError(f"No SFTP connection found for {connection_id}")
        
        sftp = self.sftp_clients[connection_id]
        with sftp.file(remote_path, 'r') as f:
            return f.read().decode()
    
    def write_remote_file(self, connection_id: str, remote_path: str, content: str):
        """Write file to remote system"""
        if connection_id not in self.sftp_clients:
            raise ValueError(f"No SFTP connection found for {connection_id}")
        
        sftp = self.sftp_clients[connection_id]
        with sftp.file(remote_path, 'w') as f:
            f.write(content)
    
    def edit_remote_file(self, connection_id: str, remote_path: str, 
                        old_content: str, new_content: str) -> bool:
        """Edit remote file by replacing content"""
        try:
            current_content = self.read_remote_file(connection_id, remote_path)
            if old_content in current_content:
                updated_content = current_content.replace(old_content, new_content)
                self.write_remote_file(connection_id, remote_path, updated_content)
                return True
            return False
        except Exception as e:
            print(f"Failed to edit remote file: {e}")
            return False
    
    def list_remote_directory(self, connection_id: str, remote_path: str = '.') -> List[Dict]:
        """List directory contents on remote system"""
        if connection_id not in self.sftp_clients:
            raise ValueError(f"No SFTP connection found for {connection_id}")
        
        sftp = self.sftp_clients[connection_id]
        items = []
        
        for attr in sftp.listdir_attr(remote_path):
            items.append({
                'name': attr.filename,
                'size': attr.st_size,
                'is_directory': stat.S_ISDIR(attr.st_mode),
                'modified': attr.st_mtime
            })
        
        return items
    
    def upload_file(self, connection_id: str, local_path: str, remote_path: str) -> bool:
        """Upload file to remote system"""
        try:
            if connection_id not in self.sftp_clients:
                raise ValueError(f"No SFTP connection found for {connection_id}")
            
            sftp = self.sftp_clients[connection_id]
            sftp.put(local_path, remote_path)
            return True
        except Exception as e:
            print(f"Failed to upload file: {e}")
            return False
    
    def download_file(self, connection_id: str, remote_path: str, local_path: str) -> bool:
        """Download file from remote system"""
        try:
            if connection_id not in self.sftp_clients:
                raise ValueError(f"No SFTP connection found for {connection_id}")
            
            sftp = self.sftp_clients[connection_id]
            sftp.get(remote_path, local_path)
            return True
        except Exception as e:
            print(f"Failed to download file: {e}")
            return False
    
    def create_remote_directory(self, connection_id: str, remote_path: str) -> bool:
        """Create directory on remote system"""
        try:
            if connection_id not in self.sftp_clients:
                raise ValueError(f"No SFTP connection found for {connection_id}")
            
            sftp = self.sftp_clients[connection_id]
            sftp.mkdir(remote_path)
            return True
        except Exception as e:
            print(f"Failed to create directory: {e}")
            return False
    
    def delete_remote_file(self, connection_id: str, remote_path: str) -> bool:
        """Delete file on remote system"""
        try:
            if connection_id not in self.sftp_clients:
                raise ValueError(f"No SFTP connection found for {connection_id}")
            
            sftp = self.sftp_clients[connection_id]
            sftp.remove(remote_path)
            return True
        except Exception as e:
            print(f"Failed to delete file: {e}")
            return False
    
    def file_exists(self, connection_id: str, remote_path: str) -> bool:
        """Check if file exists on remote system"""
        try:
            if connection_id not in self.sftp_clients:
                raise ValueError(f"No SFTP connection found for {connection_id}")
            
            sftp = self.sftp_clients[connection_id]
            sftp.stat(remote_path)
            return True
        except:
            return False
    
    def get_file_info(self, connection_id: str, remote_path: str) -> Optional[Dict]:
        """Get file information from remote system"""
        try:
            if connection_id not in self.sftp_clients:
                raise ValueError(f"No SFTP connection found for {connection_id}")
            
            sftp = self.sftp_clients[connection_id]
            attr = sftp.stat(remote_path)
            
            return {
                'size': attr.st_size,
                'is_directory': stat.S_ISDIR(attr.st_mode),
                'modified': attr.st_mtime,
                'permissions': stat.filemode(attr.st_mode)
            }
        except Exception as e:
            print(f"Failed to get file info: {e}")
            return None
    
    def sync_directory(self, connection_id: str, local_dir: str, remote_dir: str, 
                      direction: str = 'up') -> bool:
        """Sync directories between local and remote"""
        try:
            if direction == 'up':
                # Upload local to remote
                for root, dirs, files in os.walk(local_dir):
                    relative_path = os.path.relpath(root, local_dir)
                    remote_path = os.path.join(remote_dir, relative_path).replace('\\', '/')
                    
                    # Create remote directory
                    self.create_remote_directory(connection_id, remote_path)
                    
                    # Upload files
                    for file in files:
                        local_file = os.path.join(root, file)
                        remote_file = os.path.join(remote_path, file).replace('\\', '/')
                        self.upload_file(connection_id, local_file, remote_file)
            
            elif direction == 'down':
                # Download remote to local
                remote_items = self.list_remote_directory(connection_id, remote_dir)
                for item in remote_items:
                    if item['is_directory']:
                        local_path = os.path.join(local_dir, item['name'])
                        os.makedirs(local_path, exist_ok=True)
                        self.sync_directory(connection_id, local_path, 
                                           f"{remote_dir}/{item['name']}", direction)
                    else:
                        local_path = os.path.join(local_dir, item['name'])
                        remote_path = f"{remote_dir}/{item['name']}"
                        self.download_file(connection_id, remote_path, local_path)
            
            return True
        except Exception as e:
            print(f"Failed to sync directory: {e}")
            return False
    
    def get_active_connections(self) -> List[str]:
        """Get list of active connection IDs"""
        return list(self.connections.keys())
    
    def is_connected(self, connection_id: str) -> bool:
        """Check if connection is active"""
        return connection_id in self.connections and \
               self.connections[connection_id].get_transport() is not None and \
               self.connections[connection_id].get_transport().is_active()
