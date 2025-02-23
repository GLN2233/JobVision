from django.core.management.base import BaseCommand
from jobs.spiders.job51 import Job51Spider
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '从51job爬取职位信息'

    def add_arguments(self, parser):
        parser.add_argument('keywords', nargs='+', type=str)
        parser.add_argument('--pages', type=int, default=1)

    def handle(self, *args, **options):
        spider = Job51Spider()
        keywords = options['keywords']
        pages = options['pages']

        self.stdout.write(self.style.SUCCESS(f"\n开始爬取职位信息"))
        self.stdout.write(f"关键词: {', '.join(keywords)}")
        self.stdout.write(f"页数: {pages}\n")

        for keyword in keywords:
            self.stdout.write(self.style.SUCCESS(f"\n正在爬取关键词: {keyword}"))
            for page in range(1, pages + 1):
                self.stdout.write(f"\n正在爬取第 {page} 页...")
                if spider.search_jobs(keyword, page):
                    self.stdout.write(self.style.SUCCESS(f"✅ 第 {page} 页爬取成功"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ 第 {page} 页爬取失败"))
            
        # 打印统计信息
        from jobs.models import RawJob
        from django.utils import timezone
        from datetime import datetime, time
        
        today_start = datetime.combine(timezone.now().date(), time.min)
        today_end = datetime.combine(timezone.now().date(), time.max)
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("爬取统计"))
        self.stdout.write(f"今日爬取: {RawJob.objects.filter(created_at__range=(today_start, today_end)).count()} 条")
        self.stdout.write(f"待处理: {RawJob.objects.filter(status='new').count()} 条")
        self.stdout.write(f"处理失败: {RawJob.objects.filter(status='failed').count()} 条")
        self.stdout.write("="*50 + "\n") 