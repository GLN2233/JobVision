document.addEventListener('DOMContentLoaded', function() {
    // 测试数据
    const mockData = {
        categoryData: {
            categories: ['技术', '销售', '运营', '设计', '市场'],
            counts: [30, 25, 20, 15, 10]
        },
        salaryData: {
            ranges: ['0-5k', '5-10k', '10-15k', '15-20k', '20k+'],
            counts: [10, 20, 30, 25, 15]
        },
        locationData: {
            cities: ['北京', '上海', '广州', '深圳', '杭州'],
            counts: [35, 30, 25, 20, 15]
        },
        trendData: {
            dates: ['1月', '2月', '3月', '4月', '5月', '6月'],
            counts: [50, 60, 75, 85, 95, 100]
        }
    };

    // 职位类别分布图
    new Chart(document.getElementById('category-chart'), {
        type: 'pie',
        data: {
            labels: mockData.categoryData.categories,
            datasets: [{
                data: mockData.categoryData.counts,
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: '职位类别分布'
                }
            }
        }
    });

    // 薪资分布图
    new Chart(document.getElementById('salary-chart'), {
        type: 'bar',
        data: {
            labels: mockData.salaryData.ranges,
            datasets: [{
                label: '职位数量',
                data: mockData.salaryData.counts,
                backgroundColor: '#36A2EB'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: '薪资分布'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // 地区分布图
    new Chart(document.getElementById('location-chart'), {
        type: 'pie',
        data: {
            labels: mockData.locationData.cities,
            datasets: [{
                data: mockData.locationData.counts,
                backgroundColor: [
                    '#FF9F40', '#4BC0C0', '#FFCD56', '#FF6384', '#36A2EB'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: '地区分布'
                }
            }
        }
    });

    // 职位发布趋势图
    new Chart(document.getElementById('trend-chart'), {
        type: 'line',
        data: {
            labels: mockData.trendData.dates,
            datasets: [{
                label: '职位数量',
                data: mockData.trendData.counts,
                borderColor: '#36A2EB',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: '职位发布趋势'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
});
