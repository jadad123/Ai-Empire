import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { FileText, ExternalLink, RefreshCw, Trash2, CheckCircle, Clock, XCircle, Copy } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { articlesApi, sitesApi } from '../services/api';

export default function Articles() {
    const { t } = useTranslation();
    const [articles, setArticles] = useState([]);
    const [sites, setSites] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ site_id: '', status: '', page: 1 });
    const [total, setTotal] = useState(0);

    useEffect(() => { loadData(); }, [filters]);

    const loadData = async () => {
        try {
            const [articlesRes, sitesRes] = await Promise.all([
                articlesApi.list(filters),
                sitesApi.list()
            ]);
            setArticles(articlesRes.data.articles);
            setTotal(articlesRes.data.total);
            setSites(sitesRes.data.sites);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const handleRetry = async (article) => {
        try { await articlesApi.retry(article.id); loadData(); alert('تم إعادة المحاولة'); }
        catch { alert('فشل'); }
    };

    const handleDelete = async (article) => {
        if (!confirm('حذف المقال؟')) return;
        try { await articlesApi.delete(article.id); loadData(); } catch { }
    };

    const getStatusIcon = (status) => {
        const icons = {
            published: <CheckCircle className="w-4 h-4 text-green-500" />,
            processing: <Clock className="w-4 h-4 text-yellow-500 animate-spin" />,
            pending: <Clock className="w-4 h-4 text-purple-500" />,
            failed: <XCircle className="w-4 h-4 text-red-500" />,
            duplicate: <Copy className="w-4 h-4 text-gray-500" />
        };
        return icons[status] || null;
    };

    const getStatusBadge = (status) => {
        const badges = { published: 'badge-success', processing: 'badge-warning', pending: 'badge-pending', failed: 'badge-danger', duplicate: 'badge-info' };
        return badges[status] || 'badge-info';
    };

    const getSiteName = (id) => sites.find(s => s.id === id)?.name || '';

    if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div></div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold">{t('articles.title')}</h1>
                <Button variant="secondary" onClick={loadData}><RefreshCw className="w-4 h-4 ml-2" />تحديث</Button>
            </div>

            {/* Filters */}
            <Card className="!p-4">
                <div className="flex gap-4 flex-wrap">
                    <select className="input-field w-48" value={filters.site_id} onChange={(e) => setFilters({ ...filters, site_id: e.target.value, page: 1 })}>
                        <option value="">كل المواقع</option>
                        {sites.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                    </select>
                    <select className="input-field w-48" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })}>
                        <option value="">كل الحالات</option>
                        <option value="pending">قيد الانتظار</option>
                        <option value="processing">قيد المعالجة</option>
                        <option value="published">منشور</option>
                        <option value="failed">فشل</option>
                        <option value="duplicate">مكرر</option>
                    </select>
                    <span className="text-gray-400 self-center">الإجمالي: {total}</span>
                </div>
            </Card>

            {/* Articles Table */}
            <Card>
                <table className="w-full">
                    <thead>
                        <tr>
                            <th>العنوان</th>
                            <th>الموقع</th>
                            <th>الحالة</th>
                            <th>مصدر الصورة</th>
                            <th>التاريخ</th>
                            <th>الإجراءات</th>
                        </tr>
                    </thead>
                    <tbody>
                        {articles.map((article) => (
                            <tr key={article.id}>
                                <td>
                                    <div className="flex items-start gap-2 max-w-md">
                                        {getStatusIcon(article.status)}
                                        <span className="truncate">{article.processed_title || article.original_title}</span>
                                    </div>
                                </td>
                                <td>{getSiteName(article.site_id)}</td>
                                <td><span className={`badge ${getStatusBadge(article.status)}`}>{t(`articles.${article.status}`)}</span></td>
                                <td><span className="badge badge-info">{article.image_source}</span></td>
                                <td>{new Date(article.created_at).toLocaleDateString('ar')}</td>
                                <td>
                                    <div className="flex gap-2">
                                        {article.wp_post_url && (
                                            <a href={article.wp_post_url} target="_blank" className="p-2 hover:bg-blue-500/20 text-blue-500 rounded">
                                                <ExternalLink className="w-4 h-4" />
                                            </a>
                                        )}
                                        {article.status === 'failed' && (
                                            <button className="p-2 hover:bg-yellow-500/20 text-yellow-500 rounded" onClick={() => handleRetry(article)}>
                                                <RefreshCw className="w-4 h-4" />
                                            </button>
                                        )}
                                        <button className="p-2 hover:bg-red-500/20 text-red-500 rounded" onClick={() => handleDelete(article)}>
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {articles.length === 0 && <p className="text-center py-8 text-gray-400">{t('common.noData')}</p>}
            </Card>

            {/* Pagination */}
            {total > 20 && (
                <div className="flex justify-center gap-2">
                    <Button variant="secondary" disabled={filters.page <= 1} onClick={() => setFilters({ ...filters, page: filters.page - 1 })}>السابق</Button>
                    <span className="self-center text-gray-400">صفحة {filters.page}</span>
                    <Button variant="secondary" onClick={() => setFilters({ ...filters, page: filters.page + 1 })}>التالي</Button>
                </div>
            )}
        </div>
    );
}
