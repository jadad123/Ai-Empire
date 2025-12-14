import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
    Globe,
    FileText,
    TrendingUp,
    CheckCircle,
    Clock,
    AlertCircle,
    XCircle,
    Copy
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import Card from '../components/ui/Card';
import { dashboardApi } from '../services/api';

export default function Dashboard() {
    const { t } = useTranslation();
    const [stats, setStats] = useState(null);
    const [recent, setRecent] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [statsRes, recentRes, chartRes] = await Promise.all([
                dashboardApi.stats(),
                dashboardApi.recent(10),
                dashboardApi.chart(7)
            ]);
            setStats(statsRes.data);
            setRecent(recentRes.data.articles);
            setChartData(chartRes.data.data);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'published': return <CheckCircle className="w-4 h-4 text-green-500" />;
            case 'processing': return <Clock className="w-4 h-4 text-yellow-500" />;
            case 'pending': return <Clock className="w-4 h-4 text-purple-500" />;
            case 'failed': return <XCircle className="w-4 h-4 text-red-500" />;
            case 'duplicate': return <Copy className="w-4 h-4 text-gray-500" />;
            default: return <AlertCircle className="w-4 h-4 text-gray-500" />;
        }
    };

    const getStatusBadge = (status) => {
        const badges = {
            published: 'badge-success',
            processing: 'badge-warning',
            pending: 'badge-pending',
            failed: 'badge-danger',
            duplicate: 'badge-info'
        };
        return badges[status] || 'badge-info';
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
            </div>
        );
    }

    const statCards = [
        {
            title: t('dashboard.totalSites'),
            value: stats?.sites?.total || 0,
            subValue: `${stats?.sites?.active || 0} ${t('common.active')}`,
            icon: Globe,
            gradient: 'from-blue-500 to-cyan-500',
            glow: 'glow'
        },
        {
            title: t('dashboard.totalArticles'),
            value: stats?.articles?.total || 0,
            subValue: `${stats?.articles?.today || 0} اليوم`,
            icon: FileText,
            gradient: 'from-purple-500 to-pink-500',
            glow: 'glow'
        },
        {
            title: t('dashboard.publishedToday'),
            value: stats?.articles?.published_today || 0,
            subValue: 'منشور',
            icon: TrendingUp,
            gradient: 'from-green-500 to-emerald-500',
            glow: 'glow-success'
        },
        {
            title: 'قيد المعالجة',
            value: stats?.articles?.by_status?.processing || 0,
            subValue: 'مقال',
            icon: Clock,
            gradient: 'from-yellow-500 to-orange-500',
            glow: 'glow-warning'
        }
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold">{t('dashboard.title')}</h1>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {statCards.map((stat, index) => (
                    <Card key={index} className={stat.glow}>
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm text-gray-400 mb-1">{stat.title}</p>
                                <p className="text-3xl font-bold">{stat.value}</p>
                                <p className="text-sm text-gray-500 mt-1">{stat.subValue}</p>
                            </div>
                            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.gradient} flex items-center justify-center`}>
                                <stat.icon className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </Card>
                ))}
            </div>

            {/* Chart and Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Chart */}
                <Card className="lg:col-span-2">
                    <h2 className="text-lg font-semibold mb-4">{t('dashboard.articlesChart')}</h2>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                                <YAxis stroke="#64748b" fontSize={12} />
                                <Tooltip
                                    contentStyle={{
                                        background: '#1e293b',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '8px'
                                    }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="created"
                                    stroke="#8b5cf6"
                                    strokeWidth={2}
                                    dot={{ fill: '#8b5cf6' }}
                                    name="تم الإنشاء"
                                />
                                <Line
                                    type="monotone"
                                    dataKey="published"
                                    stroke="#10b981"
                                    strokeWidth={2}
                                    dot={{ fill: '#10b981' }}
                                    name="تم النشر"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </Card>

                {/* Recent Activity */}
                <Card>
                    <h2 className="text-lg font-semibold mb-4">{t('dashboard.recentActivity')}</h2>
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                        {recent.length === 0 ? (
                            <p className="text-gray-500 text-center py-8">{t('common.noData')}</p>
                        ) : (
                            recent.map((article, index) => (
                                <div
                                    key={index}
                                    className="flex items-start gap-3 p-3 rounded-lg hover:bg-white/5 transition-colors"
                                >
                                    {getStatusIcon(article.status)}
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm truncate">{article.title}</p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className={`badge ${getStatusBadge(article.status)}`}>
                                                {t(`articles.${article.status}`)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </Card>
            </div>

            {/* Status Breakdown */}
            <Card>
                <h2 className="text-lg font-semibold mb-4">توزيع الحالات</h2>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {Object.entries(stats?.articles?.by_status || {}).map(([status, count]) => (
                        <div key={status} className="text-center p-4 glass-card-light rounded-lg">
                            <p className="text-2xl font-bold">{count}</p>
                            <p className="text-sm text-gray-400 mt-1">{t(`articles.${status}`)}</p>
                        </div>
                    ))}
                </div>
            </Card>
        </div>
    );
}
