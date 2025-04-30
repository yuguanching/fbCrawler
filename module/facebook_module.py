import base64

from abc import ABC, abstractmethod


class faceebookBasic(ABC):
    def __init__(self):
        self.friendzone_docid = "26791051487175741"
        self.friendzone_reqname = "ProfileCometAppCollectionListRendererPaginationQuery"
        return


class facebookFriend(faceebookBasic):
    def __init__(self, username: str, profile_url: str, user_id: str, photo_url: str):
        super(facebookFriend, self).__init__()
        self.username = username
        self.profile_url = profile_url
        self.user_id = user_id
        self.photo_url = photo_url


class facebookUser(faceebookBasic):
    def __init__(self, username: str, profile_url: str, user_id: str):
        super(facebookUser, self).__init__()
        self.username = username
        self.profile_url = profile_url
        self.user_id = user_id
        self.friendzone_id = base64.b64encode(f"app_collection:{self.user_id}:2356318349:2".encode("UTF-8")).decode("ascii")
        self.friend_data_list: list[facebookFriend] = []
