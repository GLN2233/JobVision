document.addEventListener('DOMContentLoaded', function() {
    // 获取市场报告数据
    fetch('/jobs/market-report/', {
        headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // 初始化所有图表
            const categoryChart = echarts.init(document.getElementById('category-chart'));
            const salaryChart = echarts.init(document.getElementById('salary-chart'));
            const locationChart = echarts.init(document.getElementById('location-chart'));
            const trendChart = echarts.init(document.getElementById('trend-chart'));

            // 职位类别分布饼图配置
            const categoryOption = {
                title: {
                    text: '职位类别分布',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'item',
                    formatter: '{b}: {c} ({d}%)'
                },
                series: [{
                    type: 'pie',
                    radius: '70%',
                    data: data.job_distribution.map(item => ({
                        name: item.category__name,
                        value: item.count
                    })),
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    },
                    label: {
                        show: true,
                        formatter: '{b}: {c}'
                    }
                }]
            };

            // 薪资分布柱状图配置
            const salaryOption = {
                title: {
                    text: '薪资分布',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                xAxis: {
                    type: 'category',
                    data: data.salary_distribution.map(item => item.range),
                    axisLabel: {
                        rotate: 45
                    }
                },
                yAxis: {
                    type: 'value',
                    name: '职位数量'
                },
                series: [{
                    data: data.salary_distribution.map(item => item.count),
                    type: 'bar',
                    barWidth: '60%',
                    itemStyle: {
                        color: '#91cc75'
                    },
                    label: {
                        show: true,
                        position: 'top'
                    }
                }]
            };

            // 地区分布图配置
            const locationOption = {
                title: {
                    text: '地区分布',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'item',
                    formatter: '{b}: {c}'
                },
                series: [{
                    type: 'pie',
                    radius: '70%',
                    data: data.location_distribution.map(item => ({
                        name: item.location,
                        value: item.count
                    })),
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    },
                    label: {
                        show: true,
                        formatter: '{b}: {c}'
                    }
                }]
            };

            // 职位趋势折线图配置
            const trendOption = {
                title: {
                    text: '职位发布趋势',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'axis',
                    formatter: '{b}: {c}个职位'
                },
                xAxis: {
                    type: 'category',
                    data: data.job_trend.map(item => {
                        const date = new Date(item.month);
                        return `${date.getFullYear()}年${date.getMonth() + 1}月`;
                    }),
                    axisLabel: {
                        rotate: 45
                    }
                },
                yAxis: {
                    type: 'value',
                    name: '职位数量'
                },
                series: [{
                    data: data.job_trend.map(item => item.count),
                    type: 'line',
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 8,
                    lineStyle: {
                        width: 3
                    },
                    itemStyle: {
                        color: '#5470c6'
                    },
                    label: {
                        show: true,
                        position: 'top'
                    },
                    areaStyle: {
                        opacity: 0.3
                    }
                }]
            };

            // 设置图表配置并渲染
            categoryChart.setOption(categoryOption);
            salaryChart.setOption(salaryOption);
            locationChart.setOption(locationOption);
            trendChart.setOption(trendOption);

            // 响应式调整
            window.addEventListener('resize', function() {
                categoryChart.resize();
                salaryChart.resize();
                locationChart.resize();
                trendChart.resize();
            });
        })
        .catch(error => {
            console.error('获取市场报告数据失败:', error);
            // 显示错误信息给用户
            alert('加载市场报告数据失败，请刷新页面重试。');
        });
});