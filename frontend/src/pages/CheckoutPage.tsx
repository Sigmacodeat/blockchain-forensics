import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BTCInvoiceCheckout } from '@/components/BTCInvoiceCheckout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, CheckCircle } from 'lucide-react';

export const CheckoutPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paymentCompleted, setPaymentCompleted] = useState(false);

  // Fetch invoice details on mount
  useEffect(() => {
    if (!orderId) {
      setError('Keine Order-ID gefunden');
      setLoading(false);
      return;
    }

    fetchInvoiceDetails();
  }, [orderId]);

  const fetchInvoiceDetails = async () => {
    try {
      const response = await fetch(`/api/v1/crypto-payments/invoice/${orderId}`);
      if (!response.ok) {
        if (response.status === 404) {
          setError('Invoice nicht gefunden');
        } else {
          setError('Fehler beim Laden der Invoice');
        }
        return;
      }

      const data = await response.json();
      setInvoice(data);
    } catch (err) {
      setError('Netzwerk-Fehler beim Laden der Invoice');
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentSuccess = (payment: any) => {
    setPaymentCompleted(true);
    // Could redirect to success page or show success message
    setTimeout(() => {
      navigate('/dashboard'); // Redirect to dashboard after successful payment
    }, 3000);
  };

  const handlePaymentExpire = () => {
    setError('Die Zahlungsfrist ist abgelaufen. Bitte erstellen Sie eine neue Zahlung.');
  };

  const handlePaymentError = (errorMsg: string) => {
    setError(errorMsg);
  };

  const createNewInvoice = () => {
    navigate('/pricing'); // Redirect to pricing page to create new invoice
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-6">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2">Lade Checkout...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error && !paymentCompleted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ArrowLeft className="h-5 w-5" />
              Checkout Fehler
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            <div className="flex gap-2">
              <Button onClick={() => navigate('/pricing')} variant="outline">
                Zurück zu Preisen
              </Button>
              <Button onClick={createNewInvoice}>
                Neue Zahlung
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (paymentCompleted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-6 text-center space-y-4">
            <CheckCircle className="h-16 w-16 text-green-600 mx-auto" />
            <div>
              <h2 className="text-2xl font-bold text-green-600">Zahlung erfolgreich!</h2>
              <p className="text-gray-600 mt-2">
                Ihre Subscription wurde aktiviert. Sie werden in Kürze weitergeleitet...
              </p>
            </div>
            <Button onClick={() => navigate('/dashboard')} className="w-full">
              Zum Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <Button
              onClick={() => navigate('/pricing')}
              variant="ghost"
              className="mb-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Zurück zu Preisen
            </Button>
            <h1 className="text-3xl font-bold text-gray-900">BTC Checkout</h1>
            <p className="text-gray-600 mt-2">
              Sichere Zahlung mit Bitcoin für Ihre Blockchain-Forensics Subscription
            </p>
          </div>

          {/* Invoice Summary */}
          {invoice && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Bestellübersicht</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-medium capitalize">{invoice.plan_name} Plan</p>
                    <p className="text-sm text-gray-600">Order ID: {invoice.order_id}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">{invoice.expected_amount_btc} BTC</p>
                    <p className="text-sm text-gray-600">≈ ${(
                      parseFloat(String(invoice.expected_amount_btc || '0')) * 45000
                    ).toFixed(2)} USD</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* BTC Invoice Checkout Component */}
          {orderId && (
            <BTCInvoiceCheckout
              orderId={orderId}
              onSuccess={handlePaymentSuccess}
              onExpire={handlePaymentExpire}
              onError={handlePaymentError}
            />
          )}

          {/* Security Notice */}
          <Card className="mt-6">
            <CardContent className="p-4">
              <Alert>
                <AlertDescription>
                  <strong>Sicherheitshinweis:</strong> Ihre BTC-Adresse wird nur für diese Zahlung verwendet.
                  Verwenden Sie eine vertrauenswürdige BTC-Wallet und überprüfen Sie die Adresse vor dem Senden.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;
