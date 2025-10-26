import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Mail, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { emailMarketingService } from '@/services/emailMarketing';

interface NewsletterSignupProps {
  variant?: 'inline' | 'card';
  className?: string;
}

const NewsletterSignup: React.FC<NewsletterSignupProps> = ({ variant = 'card', className }) => {
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setIsLoading(true);
    try {
      const result = await emailMarketingService.subscribeToNewsletter({
        email: email.trim(),
        firstName: firstName.trim() || undefined,
      });

      if (result.success) {
        setIsSubscribed(true);
        toast.success('Vielen Dank für Ihr Interesse! Sie erhalten bald unsere neuesten Updates.');
        setEmail('');
        setFirstName('');
      } else {
        toast.error(result.message);
      }
    } catch (error) {
      toast.error('Es gab ein Problem beim Abonnieren. Bitte versuchen Sie es später erneut.');
    } finally {
      setIsLoading(false);
    }
  };

  if (variant === 'inline') {
    return (
      <div className={`flex gap-2 ${className}`}>
        <Input
          type="email"
          placeholder="Ihre E-Mail-Adresse"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="flex-1"
          disabled={isLoading}
        />
        <Button
          type="submit"
          onClick={handleSubmit}
          disabled={isLoading || !email.trim()}
          className="shrink-0"
        >
          {isLoading ? '...' : 'Abonnieren'}
        </Button>
      </div>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Mail className="w-5 h-5" />
          Newsletter abonnieren
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isSubscribed ? (
          <div className="text-center py-4">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Vielen Dank!</h3>
            <p className="text-muted-foreground">
              Sie haben sich erfolgreich für unseren Newsletter angemeldet.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="firstName">Vorname (optional)</Label>
              <Input
                id="firstName"
                type="text"
                placeholder="Ihr Vorname"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div>
              <Label htmlFor="email">E-Mail-Adresse *</Label>
              <Input
                id="email"
                type="email"
                placeholder="ihre.email@beispiel.de"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                required
              />
            </div>
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading || !email.trim()}
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Wird angemeldet...
                </>
              ) : (
                <>
                  <Mail className="w-4 h-4 mr-2" />
                  Newsletter abonnieren
                </>
              )}
            </Button>
            <p className="text-xs text-muted-foreground text-center">
              Wir respektieren Ihre Privatsphäre. Abmeldung jederzeit möglich.
            </p>
          </form>
        )}
      </CardContent>
    </Card>
  );
};

export default NewsletterSignup;
