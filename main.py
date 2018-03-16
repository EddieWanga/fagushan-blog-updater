import json

import requests
import glob
import os
import docx
import time

import tqdm as tqdm


class Blog(object):
    def __init__(self):
        self.session = requests.Session()

    def login(self):
        login_url = "http://ddyp.buyersline.com.tw/_i/index.php?r=auth/login"
        self.session.get(login_url)
        login_creds = {'login_account': 'ddyp', 'login_password': 'ddyp123'}
        resp = self.session.post(login_url, data=login_creds)  # username and password
        login_html = resp.text  # verify that we logged in

    def upload_photo(self, image_path):
        image_name = os.path.basename(image_path)
        photo_url = "http://ddyp.buyersline.com.tw/_i/backend.php?r=experience/upload&" \
                    "path=experience&type=image&width=500&height=320&qqfile=%s" % image_name
        with open(image_path, 'rb') as bin_image:
            resp = self.session.post(photo_url, headers={"X-File-Name": image_name,
                                                         "X-Requested-With": "XMLHttpRequest",
                                                         "Origin": "http://ddyp.buyersline.com.tw"},
                                     data=bin_image)
            raw_ret_data = resp.text
            json_data = json.loads(raw_ret_data)
            return json_data['filename']

    def post(self, topic_name, activity_type_id, description, start_date, post_data, image_path):
        create_url = "http://ddyp.buyersline.com.tw/_i/backend.php?r=experience/create"

        image_name = os.path.basename(image_path)

        uploaded_image_name = self.upload_photo(image_path)
        filtered_post_data = filter(lambda x: x != "", post_data)

        # post_data == # [ ... , ... , ... ]
        # filtered_post_data = []
        # for post_row in post_data:
        #     if post_row != "":
        #         filtered_post_data.append(post_row)


        raw_html_encoded = list(map(lambda x: "<p>%s</p>" % x, filtered_post_data))
        raw_html_encoded[0] = raw_html_encoded[0].replace("<p>", "<p style=\"text-align: center;\">")

        html_encoded = "\n".join(raw_html_encoded)
        post_data = {
            'pic1': uploaded_image_name,
            'file': image_name,
            'topic': topic_name,
            'field_tmp': description,
            'class_id': activity_type_id,
            'member_id': '13',
            'start_date': start_date,
            'is_enable': '1',
            'detail': '',
            'field_data': html_encoded
        }
        resp = self.session.post(create_url, data=post_data)  # , files=f)
        create_html = resp.text


def get_doc_list():
    base_path = "/Users/tamu/dev/projects/ddm/fagushan-blog-updater/data/organize-note2"
    docx_glob = glob.glob(os.path.join(base_path, "*", "*.docx"))
    return docx_glob


activity_type_to_id = {
    "義工服務": "4",
    "生命關懷": "5",
    "兒少教育": "6",
    "偏鄉教育": "7",
    "禪修體驗": "8",
    "營隊活動": "9",
    "常態課程": "10",
}

activity_name_to_activity_type = {"【全球信眾大會心得】": "營隊活動",
                                  "【萬行菩薩 佛國巡禮心得】": "營隊活動",
                                  "【萬行菩薩 】": "營隊活動",
                                  "【悟吧! 二日營 】": "營隊活動",
                                  "【冬季青年卓越禪修營 】": "營隊活動",
                                  "【菩薩戒護戒 】": "營隊活動",
                                  "【台南青年二日營】": "營隊活動",
                                  "【悟吧!二日營】": "營隊活動",
                                  "【世界公民領導力工作坊】": "常態課程",
                                  "【青年禪七】": "禪修體驗",
                                  "【夏季卓越禪修營】": "營隊活動",
                                  "【快樂學佛人】": "常態課程",
                                  "【社青禪修營】": "營隊活動",
                                  "【悅眾成長營】": "營隊活動",
                                  "【水陸法會送聖 】": "營隊活動",
                                  "【精進禪七 】": "禪修體驗",
                                  "【青年禪七 】": "禪修體驗",
                                  "【高雄冬季青年營 】": "營隊活動",
                                  "【冬季卓越禪修營 】": "營隊活動",
                                  "【菩薩戒 】": "營隊活動",
                                  "【悟吧!二日營：生命關懷工作坊 】": "營隊活動",
                                  "【社青禪修營 】": "營隊活動"}


class PostData:
    def __init__(self, doc_path):
        self.doc_path = doc_path
        self.doc_name, _ = os.path.splitext(os.path.basename(doc_path)) #split-filename

    @property
    def date(self):
        base_name = self.doc_name.split("_")[0]
        dt = "%s-%s-%s" % (base_name[0:4], base_name[4:6], base_name[6:8])
        return dt

    @property
    def activity_type_id(self):
        activity_name = self.activity_name
        activity_type_name = activity_name_to_activity_type[activity_name]
        activity_type_id = activity_type_to_id[activity_type_name]
        return activity_type_id

    @property
    def activity_name(self):
        base_name = self.doc_name[9:].strip()
        end_index = base_name.find("】")
        if end_index < 0:
            end_index = base_name.find("(")
        else:
            end_index += 1
        activity_name = base_name[0:end_index].strip()
        if not activity_name.startswith("【"):
            activity_name = "【" + activity_name
        if not activity_name.endswith("】"):
            activity_name += "】"
        return activity_name

    @property
    def student_name(self):
        base_name = self.doc_name[10:].strip()
        start_index = base_name.find("(") + 1
        student_name = base_name[start_index:-1].strip()
        return student_name

    @property
    def description(self):
        data = self.data
        raw_data = "".join(data)
        descrip = raw_data[:26].strip() + "..."
        return descrip

    @property
    def data(self):
        doc = docx.Document(self.doc_path)
        raw_data = []
        for para in doc.paragraphs:
            raw_data.append(para.text.strip())
        return raw_data

    @property
    def image_path(self):
        base_path = os.path.dirname(self.doc_path)
        images = glob.glob(os.path.join(base_path, "*.JPG")) + glob.glob(os.path.join(base_path, "*.jpg"))
        if len(images) <= 0:
            return None
        first_image = images[0]
        return first_image

    def __repr__(self):
        return "Date: %s Title: %s Student: %s Image: %s" % (
            self.date, self.activity_name, self.student_name, self.image_path)


def main():
    # lonin
    b = Blog()
    b.login()
    docs = get_doc_list()
    for i, doc in enumerate(tqdm.tqdm(docs)):
        if i < 47:
            continue
        pd = PostData(doc)
        # print(pd)
        # print(pd.data)
        if pd.image_path is None:
            continue

        try:
            b.post(pd.activity_name + pd.student_name, pd.activity_type_id, pd.description, pd.date, pd.data, pd.image_path)
        except Exception as e:
            print("FAILURE -- %s" % pd)


if __name__ == "__main__":
    main()
