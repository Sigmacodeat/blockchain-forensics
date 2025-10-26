import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

export interface EmailContact {
  email: string;
  firstName?: string;
  lastName?: string;
  tags?: string[];
  customFields?: Record<string, any>;
}

export interface EmailCampaign {
  id: string;
  name: string;
  subject: string;
  status: 'draft' | 'scheduled' | 'sending' | 'sent';
  recipientCount: number;
  sentAt?: string;
  createdAt: string;
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  htmlContent: string;
  textContent?: string;
  createdAt: string;
}

export class EmailMarketingService {
  private static instance: EmailMarketingService;

  static getInstance(): EmailMarketingService {
    if (!EmailMarketingService.instance) {
      EmailMarketingService.instance = new EmailMarketingService();
    }
    return EmailMarketingService.instance;
  }

  async subscribeToNewsletter(contact: EmailContact): Promise<{ success: boolean; message: string }> {
    try {
      const response = await axios.post(`${API_BASE}/api/v1/marketing/newsletter/subscribe`, contact);
      return { success: true, message: 'Successfully subscribed to newsletter' };
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to subscribe'
      };
    }
  }

  async unsubscribeFromNewsletter(email: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await axios.post(`${API_BASE}/api/v1/marketing/newsletter/unsubscribe`, { email });
      return { success: true, message: 'Successfully unsubscribed from newsletter' };
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to unsubscribe'
      };
    }
  }

  async trackEmailEvent(emailId: string, event: 'open' | 'click', data?: Record<string, any>): Promise<void> {
    try {
      await axios.post(`${API_BASE}/api/v1/marketing/email/track`, {
        emailId,
        event,
        timestamp: new Date().toISOString(),
        ...data
      });
    } catch (error) {
      console.warn('Failed to track email event:', error);
    }
  }

  async getCampaigns(): Promise<EmailCampaign[]> {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/marketing/campaigns`);
      return response.data.campaigns || [];
    } catch (error) {
      console.warn('Failed to fetch campaigns:', error);
      return [];
    }
  }

  async getTemplates(): Promise<EmailTemplate[]> {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/marketing/templates`);
      return response.data.templates || [];
    } catch (error) {
      console.warn('Failed to fetch templates:', error);
      return [];
    }
  }

  async createCampaign(campaign: Omit<EmailCampaign, 'id' | 'createdAt'>): Promise<EmailCampaign | null> {
    try {
      const response = await axios.post(`${API_BASE}/api/v1/marketing/campaigns`, campaign);
      return response.data.campaign;
    } catch (error) {
      console.warn('Failed to create campaign:', error);
      return null;
    }
  }

  async sendTestEmail(campaignId: string, testEmail: string): Promise<{ success: boolean; message: string }> {
    try {
      await axios.post(`${API_BASE}/api/v1/marketing/campaigns/${campaignId}/test`, { email: testEmail });
      return { success: true, message: 'Test email sent successfully' };
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to send test email'
      };
    }
  }
}

export const emailMarketingService = EmailMarketingService.getInstance();
