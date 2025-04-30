from Adaptor.RPABaseAdaptor import RPABaseAdaptor


class FacebookSourceAdaptor(RPABaseAdaptor):
    def __init__(self):
        super(FacebookSourceAdaptor, self).__init__()

    def insert_user_info(self, data):
        self.mode = self.INSERT_MODE
        self.write_data = data
        self.statement = ' INSERT IGNORE INTO facebookData.user ' \
                         ' (user_id, user_name, register_date, user_type, profile_url, porfile_photo_url) ' \
                         ' VALUES (%s, %s, %s, %s, %s, %s) '
        self.exec()

    def insert_user_article(self, data):
        self.mode = self.INSERT_MODE
        self.write_data = data
        self.statement = ' INSERT IGNORE INTO facebookData.user_articles ' \
                         ' (user_id, article_id, publish_time, share_id, comment_id, article_type, content, thumb_count, share_count, comment_count, image_url, video_url, article_url) ' \
                         ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
        self.exec()

    def insert_article_share_data(self, data):
        self.mode = self.INSERT_MODE
        self.write_data = data
        self.statement = ' INSERT IGNORE INTO facebookData.article_shares ' \
                         ' (share_event_id, user_id, article_id, feedback_id, share_time, sharer_id, sharer_name, sharer_profile_url, sharer_type, share_content, been_sharer_id, been_sharer_name, been_sharer_profile_url, share_page_url) ' \
                         ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
        self.exec()

    def get_post_info(self, tag_type, mobile_id, num):
        self.mode = self.QUERY_MODE
        self.statement = (" select j1.page_id, j1.p_id, j1.p_content "
                          " from open_source.page_content as ma "
                          " left join open_source.page_detail_info as j1 "
                          " on ma.page_id = j1.page_id "
                          f" where tag_type = '{tag_type}' and (j1.mobile_id is NULL or j1.mobile_id = '{mobile_id}') "
                          f" and j1.page_id is not NULL order by rand() limit {num}")
        self.query_conditions = []
        self.exec()
        return self.fetch_data

    def update_used_info(self, page_id, p_id, mobile_id, user_id):
        self.begin_transaction()
        self.mode = self.QUERY_MODE
        self.statement = " SELECT num " \
                         " FROM open_source.page_detail_info " \
                         f" WHERE page_id = '{page_id}' " \
                         f" AND p_id = '{p_id}' "
        self.exec()
        num = self.fetch_data[0][0]
        self.mode = self.UPDATE_MODE
        self.statement = (f" UPDATE open_source.page_detail_info "
                          f" SET num = %s, mobile_id = '{mobile_id}', user_id = '{user_id}' "
                          f" WHERE page_id = '{page_id}' AND p_id = '{p_id}'")
        self.update_data = [(num + 1,), ]
        self.exec()
        self.end_transaction()

    def get_article_id_info(self, user_id: str):
        self.mode = self.QUERY_MODE
        self.statement = (
            f" select article_id, comment_id, share_id from facebookData.user_articles where `user_id`='{user_id}' limit 0,1000000")
        self.query_conditions = []
        self.exec()
        exist_list = [data for data in self.fetch_data]
        return exist_list

    def get_article_id_info_by_date(self, user_id: str, deadline: str):
        self.mode = self.QUERY_MODE
        self.statement = (
            f" select article_id, comment_id, share_id from facebookData.user_articles where `user_id`='{user_id}' and `publish_time`>'{deadline}'")
        self.query_conditions = []
        self.exec()
        exist_list = [data for data in self.fetch_data]
        return exist_list

    def get_article_share_data(self, user_id: str):
        self.mode = self.QUERY_MODE
        self.statement = (
            f" select article_id, sharer_name, sharer_id, share_time, sharer_profile_url, sharer_type, been_sharer_name, been_sharer_profile_url, share_page_url from facebookData.article_shares where `user_id`='{user_id}' limit 0,10000000")
        self.query_conditions = []
        self.exec()
        exist_list = [data for data in self.fetch_data]
        return exist_list

    def get_article_share_data_by_certain_article(self, user_id: str, deadline: str):
        self.mode = self.QUERY_MODE
        self.statement = (
            f"select article_id, sharer_name, sharer_id, share_time, sharer_profile_url, sharer_type, been_sharer_name, been_sharer_profile_url, share_page_url from facebookData.article_shares where `user_id`='{user_id}' AND `article_id` in (select `article_id` from facebookData.user_articles where `user_id`='{user_id}' and `publish_time` > '{deadline}')")
        self.query_conditions = []
        self.exec()
        exist_list = [data for data in self.fetch_data]
        return exist_list

    def update_article_content(self, data):
        self.begin_transaction()
        self.mode = self.UPDATE_MODE
        self.statement = (f" UPDATE chinaForum.forum_article "
                          f" SET content = %s, title = %s "
                          f" WHERE article_id = %s ")
        self.update_data = data
        self.exec()
        self.end_transaction()

    def update_user_image(self, user_id, image_field, image):
        container = []
        image_tuple = (image,)
        container.append(image_tuple)
        self.begin_transaction()
        self.mode = self.UPDATE_MODE
        self.statement = (f" UPDATE facebookData.user"
                          f" SET `{image_field}`=%s"
                          f" WHERE `user_id`={user_id}")
        self.update_data = container
        self.exec()
        self.end_transaction()

    def update_article_image(self, article_id, image_field, image):
        container = []
        image_tuple = (image,)
        container.append(image_tuple)
        self.begin_transaction()
        self.mode = self.UPDATE_MODE
        self.statement = (f" UPDATE facebookData.user_articles"
                          f" SET `{image_field}`=%s"
                          f" WHERE `article_id`={article_id}")
        self.update_data = container
        self.exec()
        self.end_transaction()
