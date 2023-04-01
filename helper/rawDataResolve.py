
import traceback
import re
from ioService import writer


# 粉專與社團文章抓取共用
def __resolverEdgesPage__(edge) -> dict:

    ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')
    comet_sections_ = edge['node']['comet_sections']

    # name
    try:
        name = comet_sections_['context_layout']['story']['comet_sections']['actor_photo']['story']['actors'][0]['name']
        # creation_time
        creation_time = comet_sections_['context_layout']['story']['comet_sections']['metadata'][0]['story']['creation_time']
        # message
        try:
            message = comet_sections_['content']['story']['comet_sections'].get('message', '').get('story', '').get(
                'message', '').get('text', '') if comet_sections_['content']['story']['comet_sections'].get('message', '') else ''
        except:
            try:
                message = comet_sections_['content']['story']['comet_sections']['message']['rich_message'][0]['text']
            except:
                message = ""

        message = ILLEGAL_CHARACTERS_RE.sub(r'', message)
        # postid
        postid = comet_sections_[
            'feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['subscription_target_id']
        # actorid
        pageid = comet_sections_['context_layout']['story']['comet_sections']['actor_photo']['story']['actors'][0]['id']
        # comment_count 留言
        try:
            comment_count = comet_sections_[
                'feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['display_comments_count']['count']
        except:
            try:
                comment_count = comet_sections_[
                    'feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['total_comment_count']
            except:
                try:
                    comment_count = comet_sections_[
                        'feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['comment_list_renderer']['feedback']['comment_count']['total_count']
                except:
                    comment_count = 0

        # reaction_count 按讚
        reaction_count = comet_sections_[
            'feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['comet_ufi_summary_and_actions_renderer']['feedback']['reaction_count']['count']
        # share_count 分享
        share_count = comet_sections_[
            'feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['comet_ufi_summary_and_actions_renderer']['feedback']['share_count']['count']
        # top_reactions
        top_reactions = comet_sections_[
            'feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['comet_ufi_summary_and_actions_renderer']['feedback']['cannot_see_top_custom_reactions']['top_reactions']['edges']

        # feedback_id
        feedback_id = comet_sections_['feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['id']
        # url
        url = comet_sections_['context_layout']['story']['comet_sections']['metadata'][0]['story']['url']
    # cursor
    except:
        print("此篇文章格式不可抓取")
        writer.writeLogToFile(traceBack=traceback.format_exc())
        name = ""
        creation_time = 0
        message = ""
        postid = ""
        pageid = ""
        comment_count = ""
        reaction_count = ""
        share_count = ""
        top_reactions = ""
        feedback_id = ""
        url = ""

    # image url
    if len(comet_sections_['content']['story']['attachments']) == 0:
        image_url = ""
    else:
        try:
            attach_obj = comet_sections_['content']['story']['attachments'][0]['styles']['attachment']
            # 單張圖片
            if "media" in attach_obj:
                if "photo_image" in attach_obj['media']:
                    image_url = attach_obj['media']['photo_image']['uri']
                elif "image" in attach_obj['media']:
                    image_url = attach_obj['media']['image']['uri']
                else:
                    image_url = ""
            # 多張圖片
            elif "all_subattachments" in attach_obj:
                try:
                    image_url = attach_obj['all_subattachments']['nodes'][0]['media']['image']['uri']
                except:
                    writer.writeLogToFile(traceBack=traceback.format_exc())
                finally:
                    image_url = ""
            else:
                image_url = ""
        except:
            print("這篇文章不含圖片格式供抓取,可能是分享影片格式")
            image_url = ""

    # video_url
    try:
        video_url = comet_sections_['content']['story']['attachments'][0]['styles']['attachment']['media']['url']
    except:
        video_url = ""

    cursor = edge['cursor']

    dict_output = {
        "name": name,
        "creation_time": creation_time,
        "message": message,
        "postid": postid,
        "pageid": pageid,
        "feedback_id": feedback_id,
        "comment_count": comment_count,
        "reaction_count": reaction_count,
        "share_count": share_count,
        "top_reactions": top_reactions,
        "url": url,
        "image_url": image_url,
        "video_url": video_url,
        "cursor": cursor
    }

    return dict_output
    # return [name, creation_time, message, postid, pageid,feedback_id, comment_count, reaction_count, share_count, top_reactions,url,image_url, cursor]


def __resolverEdgesFeedback__(edge, posts_count) -> dict:
    comet_sections_ = edge['node']['comet_sections']

    # 分享者名稱
    sharer_name = comet_sections_['context_layout']['story']['comet_sections']['title']['story']['actors'][0]['name']

    # 分享時間
    try:
        create_time = comet_sections_['context_layout']['story']['comet_sections']['metadata'][0]['story']['creation_time']
    except:
        try:
            create_time = comet_sections_['context_layout']['story']['comet_sections']['metadata'][1]['story']['creation_time']
        except:
            create_time = comet_sections_['context_layout']['story']['comet_sections']['metadata'][2]['story']['creation_time']

    # 分享者id
    sharer_id = comet_sections_['context_layout']['story']['comet_sections']['title']['story']['actors'][0]['id']
    # 內容
    contents_check_point = comet_sections_['content']['story']['comet_sections']['message']
    if contents_check_point is None:
        contents = ""
    else:
        try:
            contents = contents_check_point['story']['message']['text']
        except:
            try:
                contents = contents_check_point['story']['rich_message'][0]['text']
            except:
                contents = ""

    # 被分享者可能不存在
    # 被分享者名稱(需另外處理)
    # 若是從某人分享到某個單人而非社團的話，只會有名字，不會有ＩＤ
    been_sharer_check_point = comet_sections_['context_layout']['story']['comet_sections']['title']['story']
    if 'to' in been_sharer_check_point:
        been_sharer_raw_name = been_sharer_check_point['to']['name']
        # 被分享者網址
        if edge['node']['feedback']['associated_group'] is not None:
            been_sharer_id = edge['node']['feedback']['associated_group']['id']
        else:
            been_sharer_id = ""
    else:
        been_sharer_raw_name = ""
        been_sharer_id = ""

    # 分享行為產生的單頁連結
    permalink = comet_sections_['feedback']['story']['url']
    if permalink is None:
        permalink = ""

    # cursor
    cursor = edge['cursor']

    dict_output = {
        "posts_count": str(posts_count),
        "sharer_name": sharer_name,
        "create_time": create_time,
        "sharer_id": sharer_id,
        "contents": contents,
        "been_sharer_raw_name": been_sharer_raw_name,
        "been_sharer_id": been_sharer_id,
        "permalink": permalink,
        "cursor": cursor
    }

    return dict_output
    # return [str(posts_count),sharer_name,create_time,sharer_id,contents,been_sharer_raw_name,been_sharer_id,cursor]


def __resolverEdgesSectionAbout__(edge, aboutNumber) -> dict:
    # 0:總覽，1:學歷與工作經歷，2:住過的地方，3:聯絡和基本資料，4:家人和感情狀況
    match aboutNumber:
        case 0:
            about_id_list = []
            name = "總覽"
            for obj in edge['all_collections']['nodes']:
                id = obj['id']
                about_id_list.append(id)
            dict_output = {
                "id_output": about_id_list,
                "name": name
            }
            return dict_output
        case 1:
            start_point = edge['activeCollections']['nodes'][0]['style_renderer']['profile_field_sections']
            name = "學經歷"
            work_name_list = []
            work_link_list = []
            work_date_list = []
            college_name_list = []
            college_link_list = []
            college_date_list = []
            highSchool_name_list = []
            highSchool_link_list = []
            highSchool_date_list = []

            for number in range(0, len(start_point)):
                profile_fields = start_point[number]["profile_fields"]["nodes"]
                for inner_number in range(0, len(profile_fields)):
                    if profile_fields[inner_number]['field_type'] == "null_state":
                        break
                    else:
                        match number:
                            case 0:  # 工作
                                work_name_list.append(profile_fields[inner_number]['title']['text'])
                                if len(profile_fields[inner_number]['list_item_groups']) != 0:
                                    work_date_list.append(profile_fields[inner_number]['list_item_groups'][0]['list_items'][0]['text']['text'])
                                else:
                                    work_date_list.append("")
                                if len(profile_fields[inner_number]['title']['ranges']) != 0:
                                    if profile_fields[inner_number]['title']['ranges'][0]['entity'] is None:
                                        work_link_list.append("")
                                    else:
                                        work_link_list.append(profile_fields[inner_number]['title']['ranges'][0]['entity']['url'])
                                else:
                                    work_link_list.append("")
                            case 1:  # 大專院校
                                college_name_list.append(profile_fields[inner_number]['title']['text'])
                                if len(profile_fields[inner_number]['list_item_groups']) != 0:
                                    college_date_list.append(profile_fields[inner_number]['list_item_groups'][0]['list_items'][0]['text']['text'])
                                else:
                                    college_date_list.append("")
                                if len(profile_fields[inner_number]['title']['ranges']) != 0:
                                    if profile_fields[inner_number]['title']['ranges'][0]['entity'] is None:
                                        college_link_list.append("")
                                    else:
                                        college_link_list.append(profile_fields[inner_number]['title']['ranges'][0]['entity']['url'])
                                else:
                                    college_link_list.append("")
                            case 2:  # 高中
                                highSchool_name_list.append(profile_fields[inner_number]['title']['text'])
                                if len(profile_fields[inner_number]['list_item_groups']) != 0:
                                    highSchool_date_list.append(profile_fields[inner_number]['list_item_groups'][0]['list_items'][0]['text']['text'])
                                else:
                                    highSchool_date_list.append("")
                                if len(profile_fields[inner_number]['title']['ranges']) != 0:
                                    if profile_fields[inner_number]['title']['ranges'][0]['entity'] is None:
                                        highSchool_link_list.append("")
                                    else:
                                        highSchool_link_list.append(profile_fields[inner_number]['title']['ranges'][0]['entity']['url'])
                                else:
                                    highSchool_link_list.append("")

            about_work_dict = {
                "name": work_name_list,
                "link": work_link_list,
                "date": work_date_list
            }
            about_college_dict = {
                "name": college_name_list,
                "link": college_link_list,
                "date": college_date_list
            }
            about_highSchool_dict = {
                "name": highSchool_name_list,
                "link": highSchool_link_list,
                "date": highSchool_date_list
            }
            dict_output = {
                "name": name,
                "work": about_work_dict,
                "college": about_college_dict,
                "highSchool": about_highSchool_dict
            }
            return dict_output
        case 2:
            start_point = edge['activeCollections']['nodes'][0]['style_renderer']['profile_field_sections']
            name = "居住"
            live_name_list = []
            live_type_list = []
            live_link_list = []
            for number in range(0, len(start_point)):
                profile_fields = start_point[number]["profile_fields"]["nodes"]
                for inner_number in range(0, len(profile_fields)):
                    if profile_fields[inner_number]['field_type'] == "null_state":
                        break
                    else:
                        live_name_list.append(profile_fields[inner_number]['title']['text'])
                        live_type_list.append(profile_fields[inner_number]['field_type'])  # current_city、hometown
                        if len(profile_fields[inner_number]['title']['ranges']) != 0:
                            live_link_list.append(profile_fields[inner_number]['title']['ranges'][0]['entity']['url'])
                        else:
                            live_link_list.append("")

            about_live_dict = {
                "name": live_name_list,
                "link": live_link_list,
                "type": live_type_list
            }

            dict_output = {
                "name": name,
                "live": about_live_dict
            }
            return dict_output
        case 3:
            start_point = edge['activeCollections']['nodes'][0]['style_renderer']['profile_field_sections']
            name = "社群"
            phone = ""
            email = ""
            address = ""
            gender = ""
            birthday_date = ""
            birthday_year = ""
            social_name_list = []
            social_link_list = []
            social_type_list = []

            for number in range(0, len(start_point)):
                profile_fields = start_point[number]["profile_fields"]["nodes"]
                for inner_number in range(0, len(profile_fields)):
                    if profile_fields[inner_number]['field_type'] == "null_state":
                        break
                    else:
                        match number:
                            case 0:  # 聯絡
                                match profile_fields[inner_number]['field_type']:
                                    case "other_phone":
                                        phone = profile_fields[inner_number]['title']['text']
                                    case "address":
                                        address = profile_fields[inner_number]['title']['text']
                                    case "email":
                                        email = profile_fields[inner_number]['title']['text']
                                    case _:
                                        pass
                                        # print(f"{profile_fields[inner_number]['field_type']} 不是欲收集的聯絡資料")
                            case 1:  # 社群
                                social_name_list.append(profile_fields[inner_number]['title']['text'])
                                social_type_list.append(profile_fields[inner_number]['list_item_groups'][0]['list_items'][0]['text']['text'])
                                if profile_fields[inner_number]['link_url'] is None:
                                    social_link_list.append(profile_fields[inner_number]['title']['text'])
                                else:
                                    social_link_list.append(profile_fields[inner_number]['link_url'])
                            case 2:  # 基本資料
                                match profile_fields[inner_number]['field_type']:
                                    case "gender":
                                        gender = profile_fields[inner_number]['title']['text']
                                    case "birthday":
                                        if profile_fields[inner_number]['list_item_groups'][0]['list_items'][0]['text']['text'] == "Birth date":
                                            birthday_date = profile_fields[inner_number]['title']['text']
                                        else:
                                            birthday_year = profile_fields[inner_number]['title']['text']
                                    case _:
                                        pass
                                        # print(f"{profile_fields[inner_number]['field_type']} 不是欲收集的聯絡資料")
            about_social_dict = {
                "name": social_name_list,
                "link": social_link_list,
                "type": social_type_list
            }
            dict_output = {
                "name": name,
                "phone": phone,
                "email": email,
                "gender": gender,
                "address": address,
                "birthday_date": birthday_date,
                "birthday_year": birthday_year,
                "social": about_social_dict
            }

            return dict_output
        case 4:
            start_point = edge['activeCollections']['nodes'][0]['style_renderer']['profile_field_sections']
            name = "人際"
            relationship_name_list = []
            relationship_link_list = []
            relationship_type_list = []

            for number in range(0, len(start_point)):
                profile_fields = start_point[number]["profile_fields"]["nodes"]
                for inner_number in range(0, len(profile_fields)):
                    if profile_fields[inner_number]['field_type'] == "null_state":
                        break
                    else:
                        match number:
                            case 0:  # 感情狀況
                                if len(profile_fields[inner_number]['list_item_groups']) != 0:  # 單身
                                    relationship_name_list.append(profile_fields[inner_number]['title']['text'])
                                    relationship_type_list.append("情侶")
                                    if len(profile_fields[inner_number]['title']['ranges']) != 0:
                                        relationship_link_list.append(profile_fields[inner_number]['title']['ranges'][0]['entity']['url'])
                                    else:
                                        relationship_link_list.append("")
                            case 1:  # 家人與親屬
                                relationship_name_list.append(profile_fields[inner_number]['title']['text'])

                                if len(profile_fields[inner_number]['list_item_groups']) != 0:
                                    relationship_type_list.append(profile_fields[inner_number]
                                                                  ['list_item_groups'][0]['list_items'][0]['text']['text'])
                                else:
                                    relationship_type_list.append("")

                                if len(profile_fields[inner_number]['title']['ranges']) != 0:
                                    relationship_link_list.append(profile_fields[inner_number]['title']['ranges'][0]['entity']['url'])
                                    if relationship_link_list[-1] is None:
                                        relationship_link_list[-1] = ""
                                else:
                                    relationship_link_list.append("")
            about_relationship_dict = {
                "name": relationship_name_list,
                "link": relationship_link_list,
                "type": relationship_type_list
            }

            dict_output = {
                "name": name,
                "relationship": about_relationship_dict
            }

            return dict_output
        case _:
            print(f"編號{str(aboutNumber)}為當前不需要的資料")
            return {}


def __resolverEdgesFriendzone__(edge) -> dict:
    name = edge['node']['title']['text']
    profile_url = edge['node']['url']
    cursor = edge['cursor']
    user_id = edge['node']['node']['id']

    if profile_url is None:
        profile_url = "https://www.facebook.com/profile.php?id=" + user_id

    dict_output = {
        "name": name,
        "url": profile_url,
        "userID": user_id,
        "cursor": cursor
    }

    return dict_output


def __resolverEdgesGroupMember__(edge) -> dict:
    name = edge['node']['name']
    profile_url = edge['node']['url']
    user_id = edge['node']['id']
    cursor = edge['cursor']

    if profile_url is None:
        profile_url = "https://www.facebook.com/profile.php?id=" + user_id

    dict_output = {
        "name": name,
        "url": profile_url,
        "userID": user_id,
        "cursor": cursor
    }

    return dict_output
