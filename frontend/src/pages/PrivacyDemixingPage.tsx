import React from 'react';
import Layout from '@/components/Layout';
import { TornadoDemix } from '@/components/PrivacyDemixing/TornadoDemix';

export default function PrivacyDemixingPage() {
  return (
    <div className="space-y-6">
      <TornadoDemix />
    </div>
  );
}
