from DrissionPage import ChromiumPage
import json
import time
from jobs.models import RawJob
from django.utils import timezone


class Job51Spider:
    def __init__(self):
        self.path = r'"C:\Program Files\Google\Chrome\Application\chrome.exe"'
        self.dp = ChromiumPage()

    def search_jobs(self, keyword='', max_pages=10):
        # 参数验证
        try:
            max_pages = int(max_pages)
            if max_pages <= 0:
                max_pages = 1
            elif max_pages > 50:  # 设置最大页数限制
                max_pages = 50
        except (ValueError, TypeError):
            max_pages = 10  # 如果参数无效，使用默认值

        # 构建带有搜索关键词的URL
        search_url = f'https://we.51job.com/pc/search?keyword={keyword}&searchType=2&sortType=0&metro='
        self.dp.get(search_url)

        # 等待页面加载完成
        self.dp.wait.ele_displayed('.joblist-item', timeout=10)

        jobs_data = []
        current_page = 1

        while current_page <= max_pages:
            print(f'正在爬取第{current_page}页...')
            divs = self.dp.eles('.joblist-item')

            for div in divs:
                try:
                    info = div.ele('css:.joblist-item-job').attr('sensorsdata')
                    if info:
                        # 解析JSON数据
                        job_info = json.loads(info)
                        # 提取标签信息
                        tags = [tag.attr('title') for tag in div.eles('css:.tags > div[title]')]
                        # 提取关键信息
                        job_data = {
                            'jobTitle': job_info.get('jobTitle', ''),
                            'jobSalary': job_info.get('jobSalary', ''),
                            'jobArea': job_info.get('jobArea', ''),
                            'jobYear': job_info.get('jobYear', ''),
                            'jobDegree': job_info.get('jobDegree', ''),
                            'companyName': div.ele('css:.cname.text-cut').text,
                            'tags': tags
                        }
                        jobs_data.append(job_data)

                        # 保存到数据库
                        RawJob.objects.create(
                            title=job_data['jobTitle'],
                            company=job_data['companyName'],
                            description=f"经验要求：{job_data['jobYear']}\n学历要求：{job_data['jobDegree']}\n标签：{', '.join(job_data['tags'])}",
                            location=job_data['jobArea'],
                            salary_range=job_data['jobSalary'],
                            original_url=search_url,
                            source='51job',
                            raw_data=job_data,
                            status='new'
                        )
                except Exception as e:
                    print(f'提取数据时出错: {str(e)}')
                    continue

            # 检查是否需要翻页
            if current_page < max_pages:  # 只有当当前页小于目标页数时才翻页
                next_button = self.dp.ele('.btn-next')
                if not next_button:
                    print(f'没有找到下一页按钮，已到达最后一页')
                    break

                # 点击下一页
                next_button.click()
                time.sleep(2)  # 等待页面加载
                self.dp.wait.ele_displayed('.joblist-item', timeout=10)

            current_page += 1

        return jobs_data


# 示例使用
if __name__ == '__main__':
    # 测试搜索Python相关职位，爬取3页数据
    spider = Job51Spider()
    results = spider.search_jobs('Python', max_pages=3)
    print(f'总共爬取到{len(results)}条职位信息：')
    for job in results:
        print(job)
