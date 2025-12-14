import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Rss, Link, Play, Trash2 } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import { sourcesApi, sitesApi } from '../services/api';

export default function Sources() {
    const { t } = useTranslation();
    const [sources, setSources] = useState([]);
    const [sites, setSites] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [saving, setSaving] = useState(false);
    const [formData, setFormData] = useState({
        site_id: '', name: '', type: 'rss', url: '',
        poll_interval: 10, max_articles_per_poll: 5, is_active: true
    });

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const [sourcesRes, sitesRes] = await Promise.all([sourcesApi.list(), sitesApi.list()]);
            setSources(sourcesRes.data.sources);
            setSites(sitesRes.data.sites);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
            await sourcesApi.create(formData);
            setShowModal(false);
            loadData();
        } catch (e) { alert(t('common.error')); }
        finally { setSaving(false); }
    };

    const handlePoll = async (s) => { try { await sourcesApi.poll(s.id); alert('تم بدء الاستطلاع'); } catch { alert('فشل'); } };
    const handleDelete = async (s) => { if (!confirm(`حذف ${s.name}?`)) return; try { await sourcesApi.delete(s.id); loadData(); } catch { } };
    const getSiteName = (id) => sites.find(s => s.id === id)?.name || '';

    if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div></div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold">{t('sources.title')}</h1>
                <Button onClick={() => setShowModal(true)}><Plus className="w-5 h-5 ml-2" />{t('sources.addSource')}</Button>
            </div>
            <Card>
                <table className="w-full">
                    <thead><tr><th>المصدر</th><th>الموقع</th><th>النوع</th><th>المقالات</th><th>الحالة</th><th>الإجراءات</th></tr></thead>
                    <tbody>
                        {sources.map((s) => (
                            <tr key={s.id}>
                                <td className="flex items-center gap-2">{s.type === 'rss' ? <Rss className="w-4 h-4 text-orange-500" /> : <Link className="w-4 h-4 text-blue-500" />}{s.name}</td>
                                <td>{getSiteName(s.site_id)}</td>
                                <td><span className="badge badge-info">{s.type}</span></td>
                                <td>{s.articles_count}</td>
                                <td><span className={`badge ${s.is_active ? 'badge-success' : 'badge-danger'}`}>{s.is_active ? 'نشط' : 'متوقف'}</span></td>
                                <td className="flex gap-2">
                                    <button className="p-2 hover:bg-green-500/20 text-green-500 rounded" onClick={() => handlePoll(s)}><Play className="w-4 h-4" /></button>
                                    <button className="p-2 hover:bg-red-500/20 text-red-500 rounded" onClick={() => handleDelete(s)}><Trash2 className="w-4 h-4" /></button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {sources.length === 0 && <p className="text-center py-8 text-gray-400">{t('common.noData')}</p>}
            </Card>
            <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={t('sources.addSource')}>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <select className="input-field" value={formData.site_id} onChange={(e) => setFormData({ ...formData, site_id: e.target.value })} required>
                        <option value="">اختر الموقع</option>
                        {sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                    </select>
                    <input className="input-field" placeholder="اسم المصدر" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
                    <select className="input-field" value={formData.type} onChange={(e) => setFormData({ ...formData, type: e.target.value })}>
                        <option value="rss">RSS</option><option value="url">URL</option>
                    </select>
                    <input className="input-field" placeholder="الرابط" value={formData.url} onChange={(e) => setFormData({ ...formData, url: e.target.value })} required />
                    <div className="flex gap-3"><Button type="submit" loading={saving} className="flex-1">{t('common.save')}</Button><Button variant="secondary" onClick={() => setShowModal(false)}>{t('common.cancel')}</Button></div>
                </form>
            </Modal>
        </div>
    );
}
