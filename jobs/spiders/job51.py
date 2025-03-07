from DrissionPage import ChromiumPage
import json
import time
from pypinyin import lazy_pinyin, Style
import re
from jobs.models import RawJob  # 注释掉Django模型导入
from django.utils import timezone  # 注释掉Django时区工具

class Job51Spider:
    def __init__(self):
        self.path = r'"C:\Program Files\Google\Chrome\Application\chrome.exe"'
        self.dp = ChromiumPage()

    def _convert_area_to_pinyin(self, area):
        # 将中文地区名称转换为拼音
        if not area:
            return ''
        
        # 分割城市和区域
        parts = area.split('·' if '·' in area else '-')
        city = parts[0].strip()
        
        # 转换城市名为拼音
        city_pinyin = ''.join(lazy_pinyin(city))
        
        if len(parts) > 1:
            district = parts[1].strip()
            # 处理区域名称
            if any(suffix in district for suffix in ['区', '市', '县']):
                # 移除后缀并获取对应的拼音后缀
                for suffix in ['区', '市', '县']:
                    if district.endswith(suffix):
                        district = district[:-1]
                        # 如果是区，则转换为首字母缩写
                        if suffix == '区':
                            district_pinyin = ''.join([p[0] for p in lazy_pinyin(district)]) + 'q'
                        else:
                            district_pinyin = ''.join(lazy_pinyin(district))
                        return f"{city_pinyin}-{district_pinyin}"
            else:
                # 如果没有后缀，直接转换为拼音
                district_pinyin = ''.join(lazy_pinyin(district))
                return f"{city_pinyin}-{district_pinyin}"
        
        # 只有城市名的情况
        return city_pinyin

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
            print(f'\n正在爬取第{current_page}页...')
            divs = self.dp.eles('.joblist-item')

            for div in divs:
                try:
                    info = div.ele('css:.joblist-item-job').attr('sensorsdata')
                    if info:
                        # 解析JSON数据
                        job_info = json.loads(info)
                        # 提取标签信息
                        tags = [tag.attr('title') for tag in div.eles('css:.tags > div[title]')]
                        # 构建职位详情页URL
                        job_id = job_info.get('jobId', '')
                        job_area = job_info.get('jobArea', '')
                        job_area_pinyin = self._convert_area_to_pinyin(job_area)
                        job_url = f'https://jobs.51job.com/{job_area_pinyin}/{job_id}.html' if job_id and job_area_pinyin else ''
                        # 提取关键信息
                        job_data = {
                            'jobTitle': job_info.get('jobTitle', ''),
                            'jobSalary': job_info.get('jobSalary', ''),
                            'jobArea': job_info.get('jobArea', ''),
                            'jobYear': job_info.get('jobYear', ''),
                            'jobDegree': job_info.get('jobDegree', ''),
                            'companyName': div.ele('css:.cname.text-cut').text,
                            'jobUrl': job_url,
                            'tags': tags
                        }
                        jobs_data.append(job_data)
                        
                        
                        RawJob.objects.create(
                            title=job_data['jobTitle'],
                            company=job_data['companyName'],
                            location=job_data['jobArea'],
                            salary_range=job_data['jobSalary'],
                            description=f"经验要求：{job_data['jobYear']}\n学历要求：{job_data['jobDegree']}\n职位标签：{', '.join(job_data['tags'])}",
                            source='51job',
                            original_url=job_data['jobUrl'],
                            raw_data=job_data,
                            status='new',
                            created_at=timezone.now()
                        )
                        
                        # 打印职位信息
                        # print('\n' + '='*50)
                        # print(f'职位名称：{job_data["jobTitle"]}')
                        # print(f'公司名称：{job_data["companyName"]}')
                        # print(f'工作地点：{job_data["jobArea"]}')
                        # print(f'薪资范围：{job_data["jobSalary"]}')
                        # print(f'经验要求：{job_data["jobYear"]}')
                        # print(f'学历要求：{job_data["jobDegree"]}')
                        # print(f'职位标签：{", ".join(job_data["tags"])}')
                        # print(f'详情链接：{job_data["jobUrl"]}')
                        # print('='*50)
                        
                except Exception as e:
                    print(f'提取数据时出错: {str(e)}')
                    continue

            # 检查是否需要翻页
            if current_page < max_pages:  # 只有当当前页小于目标页数时才翻页
                next_button = self.dp.ele('.btn-next')
                if not next_button:
                    print(f'\n没有找到下一页按钮，已到达最后一页')
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
    results = spider.search_jobs('Python', max_pages=1)
    print(f'\n总共爬取到{len(results)}条职位信息')
    for job in results:
        print(job)
