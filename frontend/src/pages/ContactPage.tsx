import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, MapPin, Phone, Send, CheckCircle, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import axios from 'axios';
import { fadeUp, staggerContainer, staggerItem, scaleUp, defaultViewport } from '@/utils/animations';

const ContactPage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
    country: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [ticketId, setTicketId] = useState('');
  const [estimatedTime, setEstimatedTime] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus('idle');

    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/support/contact`, {
        ...formData,
        language: i18n.language,
      });

      if (response.data.success) {
        setSubmitStatus('success');
        setTicketId(response.data.ticket_id);
        setEstimatedTime(response.data.estimated_response_time);
        // Reset form
        setFormData({ name: '', email: '', subject: '', message: '', country: '' });
      } else {
        setSubmitStatus('error');
      }
    } catch (error) {
      console.error('Contact form error:', error);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const countries = [
    { code: 'DE', name: 'Deutschland' },
    { code: 'AT', name: 'Österreich' },
    { code: 'CH', name: 'Schweiz' },
    { code: 'US', name: 'United States' },
    { code: 'GB', name: 'United Kingdom' },
    { code: 'FR', name: 'France' },
    { code: 'ES', name: 'Spain' },
    { code: 'IT', name: 'Italy' },
    { code: 'NL', name: 'Netherlands' },
    { code: 'BE', name: 'Belgium' },
    { code: 'JP', name: 'Japan' },
    { code: 'KR', name: 'South Korea' },
    { code: 'CN', name: 'China' },
    { code: 'SG', name: 'Singapore' },
    { code: 'AU', name: 'Australia' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <motion.div 
          variants={fadeUp}
          initial="initial"
          animate="whileInView"
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            {t('contact.title', 'Kontaktieren Sie uns')}
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
            {t('contact.subtitle', 'Haben Sie Fragen? Unser Support-Team hilft Ihnen gerne weiter.')}
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Contact Info Cards */}
          <motion.div 
            variants={staggerContainer}
            initial="initial"
            whileInView="whileInView"
            viewport={defaultViewport}
            className="lg:col-span-1 space-y-6"
          >
            {/* Email Card */}
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6 border border-slate-200 dark:border-slate-700">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Mail className="w-6 h-6 text-white" />
                </div>
                <h3 className="ml-4 text-lg font-semibold text-slate-900 dark:text-white">
                  E-Mail
                </h3>
              </div>
              <a 
                href="mailto:support@blockchain-forensics.com"
                className="text-primary-600 dark:text-primary-400 hover:underline"
              >
                support@blockchain-forensics.com
              </a>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                {t('contact.response_time', 'Antwortzeit: 24-48 Stunden')}
              </p>
            </div>

            {/* Location Card */}
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6 border border-slate-200 dark:border-slate-700">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center">
                  <MapPin className="w-6 h-6 text-white" />
                </div>
                <h3 className="ml-4 text-lg font-semibold text-slate-900 dark:text-white">
                  Standort
                </h3>
              </div>
              <p className="text-slate-600 dark:text-slate-300">
                Wien, Österreich<br />
                EU 🇪🇺
              </p>
            </div>

            {/* Chatbot Info */}
            <div className="bg-gradient-to-br from-primary-50 to-purple-50 dark:from-slate-800 dark:to-slate-700 rounded-lg p-6 border border-primary-200 dark:border-primary-700">
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                💡 {t('contact.chatbot_tip', 'Sofortige Hilfe')}
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300">
                {t('contact.chatbot_text', 'Nutzen Sie unseren AI-Chatbot unten rechts für sofortige Antworten 24/7!')}
              </p>
            </div>
          </motion.div>

          {/* Contact Form */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2"
          >
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-8 border border-slate-200 dark:border-slate-700">
              {submitStatus === 'success' ? (
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="text-center py-12"
                >
                  <div className="w-20 h-20 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-6">
                    <CheckCircle className="w-12 h-12 text-green-600 dark:text-green-400" />
                  </div>
                  <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
                    ✅ {t('contact.success_title', 'Nachricht gesendet!')}
                  </h3>
                  <p className="text-slate-600 dark:text-slate-300 mb-2">
                    {t('contact.ticket_id', 'Ihre Ticket-ID')}: <strong>#{ticketId}</strong>
                  </p>
                  <p className="text-slate-600 dark:text-slate-300 mb-6">
                    {t('contact.estimated_time', 'Geschätzte Antwortzeit')}: <strong>{estimatedTime}</strong>
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {t('contact.confirmation_email', 'Eine Bestätigungs-E-Mail wurde an Ihre Adresse gesendet.')}
                  </p>
                  <Button
                    onClick={() => setSubmitStatus('idle')}
                    size="lg"
                    variant="default"
                    className="mt-8"
                  >
                    {t('contact.send_another', 'Neue Nachricht senden')}
                  </Button>
                </motion.div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      {t('contact.name', 'Name')} *
                    </label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      required
                      minLength={2}
                      maxLength={100}
                      className="w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
                      placeholder={t('contact.name_placeholder', 'Ihr vollständiger Name')}
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      {t('contact.email', 'E-Mail')} *
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
                      placeholder={t('contact.email_placeholder', 'ihre.email@example.com')}
                    />
                  </div>

                  {/* Country */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      {t('contact.country', 'Land')}
                    </label>
                    <select
                      name="country"
                      value={formData.country}
                      onChange={handleChange}
                      className="w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
                    >
                      <option value="">{t('contact.country_select', 'Land auswählen...')}</option>
                      {countries.map(country => (
                        <option key={country.code} value={country.code}>
                          {country.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Subject */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      {t('contact.subject', 'Betreff')} *
                    </label>
                    <input
                      type="text"
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      required
                      minLength={5}
                      maxLength={200}
                      className="w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
                      placeholder={t('contact.subject_placeholder', 'Kurze Beschreibung Ihres Anliegens')}
                    />
                  </div>

                  {/* Message */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      {t('contact.message', 'Nachricht')} *
                    </label>
                    <textarea
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      required
                      minLength={10}
                      maxLength={5000}
                      rows={6}
                      className="w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent transition resize-none"
                      placeholder={t('contact.message_placeholder', 'Beschreiben Sie Ihr Anliegen im Detail...')}
                    />
                  </div>

                  {/* Error Message */}
                  {submitStatus === 'error' && (
                    <motion.div
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="flex items-center gap-2 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400"
                    >
                      <AlertCircle className="w-5 h-5 flex-shrink-0" />
                      <span>{t('contact.error', 'Fehler beim Senden. Bitte versuchen Sie es erneut.')}</span>
                    </motion.div>
                  )}

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    size="xl"
                    variant="premium"
                    className="w-full"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span className="ml-2">{t('contact.sending', 'Wird gesendet...')}</span>
                      </>
                    ) : (
                      <>
                        <Send className="w-5 h-5" />
                        <span className="ml-2">{t('contact.submit', 'Nachricht senden')}</span>
                      </>
                    )}
                  </Button>

                  <p className="text-xs text-slate-500 dark:text-slate-400 text-center">
                    {t('contact.privacy_notice', 'Wir respektieren Ihre Privatsphäre und geben Ihre Daten nicht an Dritte weiter.')}
                  </p>
                </form>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ContactPage;
