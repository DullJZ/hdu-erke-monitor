"""
杭州电子科技大学青春杭电第二课堂活动监控

activityStatus: ["-1","已保存"],["0","待系统审核"],["1","系统审核不通过"],["2","待审核员审核"],["3","待完结"],["4","完结审核中"],["5","完结通过"],["6","完结不通过"],["7","已取消"],["8","报名中"],["9","即将开始"],["10","签到中"],["11","待签退"],["12","签退中"],["13","审核员审核不通过"]
activityType: ["1","讲座"],["2","晚会"],["3","竞赛"],["4","宣传"],["5","服务"]
activityContent: ["1","思想引领"],["2","创新创业"],["3","美育"],["4","体育"],["5","公益实践"],["6","劳动教育"],["7","其他"]
"""

import requests
import json
import time
import hashlib
from typing import Dict, List, Optional

# 配置项
CONFIG = {
    "check_interval": 60,  # 检查间隔（秒）
    "webhook_url": "YOUR_WEBHOOK_URL",  # Webhook URL
    "key_word": "YOUR_KEY_WORD", # Webhook 需要的关键字
    "activity_type": "1",  # 活动类型（讲座）
    "activity_status": "8"  # 活动状态（报名中）
}

class ActivityMonitor:
    def __init__(self):
        self.last_activities: Dict[str, dict] = {}
        
    def get_activity_list(self) -> dict:
        url = "https://erke.hdu.edu.cn/prod-api/wechat/activityList?pageSize=10&pageNum=1"
        headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "token",
            "Connection": "keep-alive",
            "Origin": "https://erke.hdu.edu.cn",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/134.0.0.0",
            "authorization": "YOUR_JWT_TOKEN",
            "content-type": "application/json;charset=UTF-8",
        }
        data = {
            "activityType": CONFIG["activity_type"],
            "activityStatus": CONFIG["activity_status"],
            "hostName": ""
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()

    def get_activity_hash(self, activity: dict) -> str:
        """生成活动的唯一标识"""
        activity_str = f"{activity['activityName']}{activity['activityStartTime']}{activity['position']}"
        return hashlib.md5(activity_str.encode()).hexdigest()

    def send_webhook(self, activity: dict) -> None:
        """发送webhook通知"""
        webhook_data = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"{CONFIG['key_word']}新活动通知",
                "text": f"### 新活动：{activity['activityName']}\n" \
                        f"- 开始时间：{activity['activityStartTime']}\n" \
                        f"- 活动地点：{activity['position']}\n" \
                        f"- 活动内容：{activity['txt']}\n" \
                        f"- 报名人数：{activity['applyCount']}\n"
            }
        }
        try:
            requests.post(CONFIG["webhook_url"], json=webhook_data)
            print(f"已推送新活动：{activity['activityName']}")
        except Exception as e:
            print(f"推送失败：{str(e)}")

    def check_new_activities(self) -> None:
        """检查新活动"""
        try:
            activities = self.get_activity_list()
            now = time.time()
            
            for activity in activities["rows"]:
                # 只关注未来的活动
                activity_time = time.mktime(time.strptime(activity["activityStartTime"], "%Y-%m-%d %H:%M:%S"))
                if activity_time < now:
                    continue
                    
                activity_hash = self.get_activity_hash(activity)
                if activity_hash not in self.last_activities:
                    self.send_webhook(activity)
                    self.last_activities[activity_hash] = activity
                    
            # 清理过期活动缓存
            self.last_activities = {k: v for k, v in self.last_activities.items()
                                  if time.mktime(time.strptime(v["activityStartTime"], "%Y-%m-%d %H:%M:%S")) > now}
                                  
        except Exception as e:
            print(f"检查活动失败：{str(e)}")

    def run(self) -> None:
        """运行监控"""
        print(f"开始监控活动，检查间隔：{CONFIG['check_interval']}秒")
        while True:
            self.check_new_activities()
            time.sleep(CONFIG["check_interval"])

def main():
    monitor = ActivityMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
