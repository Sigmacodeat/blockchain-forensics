import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CalendarDays, Users, Eye, MousePointer, TrendingUp, Download } from 'lucide-react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface AnalyticsDashboardProps {
  className?: string;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ className }) => {
  // Mock data - in real implementation, fetch from API
  const kpiData = {
    totalEvents: 15420,
    uniqueUsers: 2847,
    pageviews: 8956,
    avgSessionDuration: '4:32'
  };

  const trafficSources = [
    { source: 'Direct', visitors: 1247, percentage: 43.8 },
    { source: 'Google', visitors: 892, percentage: 31.4 },
    { source: 'Social Media', visitors: 423, percentage: 14.9 },
    { source: 'Referral', visitors: 285, percentage: 10.0 }
  ];

  const topPages = [
    { path: '/dashboard', views: 2847, percentage: 31.7 },
    { path: '/investigator', views: 1923, percentage: 21.4 },
    { path: '/cases', views: 1456, percentage: 16.2 },
    { path: '/', views: 1234, percentage: 13.7 }
  ];

  const userBehavior = {
    avgScrollDepth: 68,
    avgTimeOnPage: '3:24',
    bounceRate: 34.2,
    clickThroughRate: 12.8
  };

  const lineChartData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Page Views',
        data: [1200, 1350, 1180, 1420, 1680, 1520, 1380],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Unique Users',
        data: [890, 920, 850, 980, 1100, 950, 920],
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const barChartData = {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
    datasets: [
      {
        label: 'Active Users',
        data: [120, 80, 340, 520, 680, 420],
        backgroundColor: 'rgba(59, 130, 246, 0.6)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1,
      },
    ],
  };

  const doughnutData = {
    labels: trafficSources.map(s => s.source),
    datasets: [
      {
        data: trafficSources.map(s => s.visitors),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">Comprehensive insights into user behavior and performance</p>
        </div>
        <div className="flex items-center gap-4">
          <Select defaultValue="7d">
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1d">Last Day</SelectItem>
              <SelectItem value="7d">Last 7 Days</SelectItem>
              <SelectItem value="30d">Last 30 Days</SelectItem>
              <SelectItem value="90d">Last 90 Days</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Events</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpiData.totalEvents.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">+12% from last period</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unique Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpiData.uniqueUsers.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">+8% from last period</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Page Views</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpiData.pageviews.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">+15% from last period</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Session</CardTitle>
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpiData.avgSessionDuration}</div>
            <p className="text-xs text-muted-foreground">+5% from last period</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Traffic Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <Line data={lineChartData} options={{ responsive: true, maintainAspectRatio: false }} height={300} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Hourly Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <Bar data={barChartData} options={{ responsive: true, maintainAspectRatio: false }} height={300} />
          </CardContent>
        </Card>
      </div>

      {/* Traffic Sources & Top Pages */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Traffic Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {trafficSources.map((source) => (
                <div key={source.source} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-blue-500" />
                    <span className="font-medium">{source.source}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      {source.visitors.toLocaleString()} ({source.percentage}%)
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <Doughnut data={doughnutData} options={{ responsive: true, maintainAspectRatio: false }} height={200} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Pages</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topPages.map((page) => (
                <div key={page.path} className="flex items-center justify-between">
                  <div className="flex flex-col">
                    <span className="font-medium">{page.path}</span>
                    <span className="text-sm text-muted-foreground">
                      {page.views.toLocaleString()} views
                    </span>
                  </div>
                  <Badge variant="secondary">{page.percentage}%</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* User Behavior */}
      <Card>
        <CardHeader>
          <CardTitle>User Behavior Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{userBehavior.avgScrollDepth}%</div>
              <p className="text-sm text-muted-foreground">Avg Scroll Depth</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{userBehavior.avgTimeOnPage}</div>
              <p className="text-sm text-muted-foreground">Avg Time on Page</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{userBehavior.bounceRate}%</div>
              <p className="text-sm text-muted-foreground">Bounce Rate</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{userBehavior.clickThroughRate}%</div>
              <p className="text-sm text-muted-foreground">Click-through Rate</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsDashboard;
