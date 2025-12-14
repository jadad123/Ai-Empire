import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Globe, MoreVertical, Check, X, RefreshCw, Trash2, Edit } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import { sitesApi } from '../services/api';

export default function Sites() {
    const { t } = useTranslation();
    const [sites, setSites] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingSite, setEditingSite] = useState(null);
    const [saving, setSaving] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        url: '',
        wp_username: '',
        wp_app_password: '',
        target_language: 'ar',
        velocity_mode: 'news',
        category_map: '',
        bing_cookie: '',
        watermark_text: '',
        is_active: true
    });

    useEffect(() => {
        loadSites();
    }, []);

    const loadSites = async () => {
        try {
            const response = await sitesApi.list();
            setSites(response.data.sites);
        } catch (error) {
            console.error('Failed to load sites:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);

        try {
            // Parse category map from text
            let categoryMap = {};
            if (formData.category_map) {
                formData.category_map.split('\n').forEach(line => {
                    const [id, name] = line.split(':').map(s => s.trim());
                    if (id && name) categoryMap[id] = name;
                });
            }

            const payload = {
                ...formData,
                category_map: categoryMap
            };

            if (editingSite) {
                await sitesApi.update(editingSite.id, payload);
            } else {
                await sitesApi.create(payload);
            }

            setShowModal(false);
            resetForm();
            loadSites();
        } catch (error) {
            console.error('Failed to save site:', error);
            alert(t('common.error'));
        } finally {
            setSaving(false);
        }
    };

    const handleEdit = (site) => {
        setEditingSite(site);
        // Convert category map to text format
        const categoryText = Object.entries(site.category_map || {})
            .map(([id, name]) => `${id}: ${name}`)
            .join('\n');

        setFormData({
            name: site.name,
            url: site.url,
            wp_username: site.wp_username,
            wp_app_password: '',
            target_language: site.target_language,
            velocity_mode: site.velocity_mode,
            category_map: categoryText,
            bing_cookie: '',
            watermark_text: site.watermark_text || '',
            is_active: site.is_active
        });
        setShowModal(true);
    };

    const handleDelete = async (site) => {
        if (!confirm(`هل أنت متأكد من حذف ${site.name}?`)) return;

        try {
            await sitesApi.delete(site.id);
            loadSites();
        } catch (error) {
            console.error('Failed to delete site:', error);
        }
    };

    const handleTestConnection = async (site) => {
        try {
            const response = await sitesApi.testConnection(site.id);
            alert(response.data.message);
        } catch (error) {
            alert('فشل الاتصال');
        }
    };

    const handleSyncCategories = async (site) => {
        try {
            const response = await sitesApi.syncCategories(site.id);
            alert(`تم مزامنة ${response.data.count} تصنيف`);
            loadSites();
        } catch (error) {
            alert('فشل المزامنة');
        }
    };

    const resetForm = () => {
        setEditingSite(null);
        setFormData({
            name: '',
            url: '',
            wp_username: '',
            wp_app_password: '',
            target_language: 'ar',
            velocity_mode: 'news',
            category_map: '',
            bing_cookie: '',
            watermark_text: '',
            is_active: true
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold">{t('sites.title')}</h1>
                <Button onClick={() => { resetForm(); setShowModal(true); }}>
                    <Plus className="w-5 h-5 ml-2" />
                    {t('sites.addSite')}
                </Button>
            </div>

            {/* Sites Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sites.map((site) => (
                    <Card key={site.id} className="hover:border-purple-500/30 transition-colors">
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                                    <Globe className="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <h3 className="font-semibold">{site.name}</h3>
                                    <p className="text-sm text-gray-400 truncate max-w-[150px]">{site.url}</p>
                                </div>
                            </div>
                            <span className={`badge ${site.is_active ? 'badge-success' : 'badge-danger'}`}>
                                {site.is_active ? t('common.active') : t('common.inactive')}
                            </span>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-4">
                            <div className="text-center p-3 glass-card-light rounded-lg">
                                <p className="text-xl font-bold">{site.sources_count}</p>
                                <p className="text-xs text-gray-400">{t('sites.sources')}</p>
                            </div>
                            <div className="text-center p-3 glass-card-light rounded-lg">
                                <p className="text-xl font-bold">{site.articles_count}</p>
                                <p className="text-xs text-gray-400">{t('sites.articles')}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-2 text-sm text-gray-400 mb-4">
                            <span className="badge badge-info">{site.target_language.toUpperCase()}</span>
                            <span className="badge badge-pending">
                                {site.velocity_mode === 'news' ? t('sites.velocityNews') : t('sites.velocityEvergreen')}
                            </span>
                        </div>

                        <div className="flex items-center gap-2">
                            <Button
                                variant="secondary"
                                className="flex-1 !py-2 !px-3 text-sm"
                                onClick={() => handleTestConnection(site)}
                            >
                                <Check className="w-4 h-4 ml-1" />
                                اختبار
                            </Button>
                            <Button
                                variant="secondary"
                                className="flex-1 !py-2 !px-3 text-sm"
                                onClick={() => handleSyncCategories(site)}
                            >
                                <RefreshCw className="w-4 h-4 ml-1" />
                                مزامنة
                            </Button>
                            <button
                                className="p-2 rounded-lg hover:bg-white/10"
                                onClick={() => handleEdit(site)}
                            >
                                <Edit className="w-4 h-4" />
                            </button>
                            <button
                                className="p-2 rounded-lg hover:bg-red-500/20 text-red-500"
                                onClick={() => handleDelete(site)}
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    </Card>
                ))}

                {sites.length === 0 && (
                    <Card className="col-span-full text-center py-12">
                        <Globe className="w-16 h-16 mx-auto mb-4 text-gray-600" />
                        <p className="text-gray-400">{t('common.noData')}</p>
                        <Button className="mt-4" onClick={() => setShowModal(true)}>
                            {t('sites.addSite')}
                        </Button>
                    </Card>
                )}
            </div>

            {/* Add/Edit Modal */}
            <Modal
                isOpen={showModal}
                onClose={() => { setShowModal(false); resetForm(); }}
                title={editingSite ? `تعديل ${editingSite.name}` : t('sites.addSite')}
            >
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">{t('sites.siteName')}</label>
                        <input
                            type="text"
                            className="input-field"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-gray-400 mb-1">{t('sites.siteUrl')}</label>
                        <input
                            type="url"
                            className="input-field"
                            placeholder="https://example.com"
                            value={formData.url}
                            onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                            required
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">{t('sites.wpUsername')}</label>
                            <input
                                type="text"
                                className="input-field"
                                value={formData.wp_username}
                                onChange={(e) => setFormData({ ...formData, wp_username: e.target.value })}
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">{t('sites.wpPassword')}</label>
                            <input
                                type="password"
                                className="input-field"
                                placeholder={editingSite ? '••••••••' : ''}
                                value={formData.wp_app_password}
                                onChange={(e) => setFormData({ ...formData, wp_app_password: e.target.value })}
                                required={!editingSite}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">{t('sites.targetLanguage')}</label>
                            <select
                                className="input-field"
                                value={formData.target_language}
                                onChange={(e) => setFormData({ ...formData, target_language: e.target.value })}
                            >
                                <option value="ar">العربية</option>
                                <option value="en">English</option>
                                <option value="fr">Français</option>
                                <option value="es">Español</option>
                                <option value="de">Deutsch</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">{t('sites.velocityMode')}</label>
                            <select
                                className="input-field"
                                value={formData.velocity_mode}
                                onChange={(e) => setFormData({ ...formData, velocity_mode: e.target.value })}
                            >
                                <option value="news">{t('sites.velocityNews')}</option>
                                <option value="evergreen">{t('sites.velocityEvergreen')}</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm text-gray-400 mb-1">
                            {t('sites.categoryMap')}
                            <span className="text-xs text-gray-500 mr-2">(ID: Name - كل سطر)</span>
                        </label>
                        <textarea
                            className="input-field h-24"
                            placeholder="1: أخبار&#10;2: تقنية&#10;3: رياضة"
                            value={formData.category_map}
                            onChange={(e) => setFormData({ ...formData, category_map: e.target.value })}
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-gray-400 mb-1">{t('sites.bingCookie')}</label>
                        <input
                            type="text"
                            className="input-field"
                            placeholder="_U cookie value"
                            value={formData.bing_cookie}
                            onChange={(e) => setFormData({ ...formData, bing_cookie: e.target.value })}
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-gray-400 mb-1">{t('sites.watermarkText')}</label>
                        <input
                            type="text"
                            className="input-field"
                            placeholder="اسم الموقع"
                            value={formData.watermark_text}
                            onChange={(e) => setFormData({ ...formData, watermark_text: e.target.value })}
                        />
                    </div>

                    <div className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            id="is_active"
                            checked={formData.is_active}
                            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                            className="w-4 h-4 rounded"
                        />
                        <label htmlFor="is_active" className="text-sm">{t('common.active')}</label>
                    </div>

                    <div className="flex gap-3 pt-4">
                        <Button type="submit" loading={saving} className="flex-1">
                            {t('common.save')}
                        </Button>
                        <Button
                            type="button"
                            variant="secondary"
                            onClick={() => { setShowModal(false); resetForm(); }}
                        >
                            {t('common.cancel')}
                        </Button>
                    </div>
                </form>
            </Modal>
        </div>
    );
}
