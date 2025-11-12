/**
 * SuggestEditForm Component
 *
 * Allows users to submit corrections and suggestions for flight school data.
 * Includes form validation, toast notifications, and API integration.
 */

import { useState, type FormEvent } from 'react';
import { X, Send, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';

interface SuggestEditFormProps {
  schoolId?: string;
  schoolName?: string;
  onClose?: () => void;
  onSuccess?: () => void;
  className?: string;
}

interface FormData {
  name: string;
  email: string;
  phone: string;
  contactInfo: string;
  pricing: string;
  description: string;
  programs: string;
  otherCorrections: string;
}

interface ToastMessage {
  type: 'success' | 'error';
  message: string;
}

export default function SuggestEditForm({
  schoolId,
  schoolName,
  onClose,
  onSuccess,
  className = ''
}: SuggestEditFormProps) {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    phone: '',
    contactInfo: '',
    pricing: '',
    description: '',
    programs: '',
    otherCorrections: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const validateForm = (): string | null => {
    if (!formData.email.trim()) {
      return 'Email is required for verification';
    }

    if (!formData.email.includes('@')) {
      return 'Please enter a valid email address';
    }

    // Check if at least one correction field is filled
    const hasCorrections = Object.entries(formData).some(([key, value]) => {
      return !['name', 'email', 'phone'].includes(key) && value.trim().length > 0;
    });

    if (!hasCorrections) {
      return 'Please provide at least one correction or suggestion';
    }

    return null;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const validationError = validateForm();
    if (validationError) {
      setToast({ type: 'error', message: validationError });
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        schoolId: schoolId || 'general',
        schoolName: schoolName || 'Unknown School',
        submittedAt: new Date().toISOString(),
        submitter: {
          name: formData.name.trim() || undefined,
          email: formData.email.trim(),
          phone: formData.phone.trim() || undefined
        },
        corrections: {
          contactInfo: formData.contactInfo.trim() || undefined,
          pricing: formData.pricing.trim() || undefined,
          description: formData.description.trim() || undefined,
          programs: formData.programs.trim() || undefined,
          otherCorrections: formData.otherCorrections.trim() || undefined
        },
        userAgent: navigator.userAgent,
        url: window.location.href
      };

      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Submission failed: ${response.statusText}`);
      }

      const result = await response.json();

      setToast({
        type: 'success',
        message: 'Thank you for your feedback! Your suggestions help improve our data quality.'
      });

      // Reset form
      setFormData({
        name: '',
        email: '',
        phone: '',
        contactInfo: '',
        pricing: '',
        description: '',
        programs: '',
        otherCorrections: ''
      });

      // Call success callback after a delay
      setTimeout(() => {
        onSuccess?.();
        onClose?.();
      }, 3000);

    } catch (error) {
      console.error('Feedback submission error:', error);
      setToast({
        type: 'error',
        message: 'Sorry, there was an error submitting your feedback. Please try again later.'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const clearToast = () => {
    setToast(null);
  };

  return (
    <div className={`relative ${className}`}>
      {/* Toast Notification */}
      {toast && (
        <div className={`
          fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg
          ${toast.type === 'success'
            ? 'bg-green-50 border border-green-200 text-green-800'
            : 'bg-red-50 border border-red-200 text-red-800'
          }
        `}>
          {toast.type === 'success' ? (
            <CheckCircle className="w-5 h-5 text-green-600" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-600" />
          )}
          <span className="text-sm font-medium">{toast.message}</span>
          <button
            onClick={clearToast}
            className="ml-2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <Card className="max-w-2xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Suggest an Edit</h2>
            <p className="text-sm text-gray-600 mt-1">
              Help us improve our data by suggesting corrections for{' '}
              {schoolName ? <span className="font-medium">{schoolName}</span> : 'this flight school'}.
            </p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Contact Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Your Information</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Name (Optional)
                </label>
                <Input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Your name"
                  className="w-full"
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  Email <span className="text-red-500">*</span>
                </label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  placeholder="your.email@example.com"
                  className="w-full"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                Phone (Optional)
              </label>
              <Input
                id="phone"
                type="tel"
                value={formData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
                placeholder="(555) 123-4567"
                className="w-full"
              />
            </div>
          </div>

          {/* Correction Fields */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Suggested Corrections</h3>
            <p className="text-sm text-gray-600">
              Please provide specific corrections or updates for any information that needs to be changed.
            </p>

            <div className="space-y-4">
              <div>
                <label htmlFor="contactInfo" className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Information
                </label>
                <textarea
                  id="contactInfo"
                  value={formData.contactInfo}
                  onChange={(e) => handleInputChange('contactInfo', e.target.value)}
                  placeholder="Phone, email, website corrections..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-vertical"
                  rows={3}
                />
              </div>

              <div>
                <label htmlFor="pricing" className="block text-sm font-medium text-gray-700 mb-1">
                  Pricing Information
                </label>
                <textarea
                  id="pricing"
                  value={formData.pricing}
                  onChange={(e) => handleInputChange('pricing', e.target.value)}
                  placeholder="Hourly rates, package pricing, fees..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-vertical"
                  rows={3}
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                  School Description
                </label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Mission statement, specialties, facilities..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-vertical"
                  rows={3}
                />
              </div>

              <div>
                <label htmlFor="programs" className="block text-sm font-medium text-gray-700 mb-1">
                  Programs & Training
                </label>
                <textarea
                  id="programs"
                  value={formData.programs}
                  onChange={(e) => handleInputChange('programs', e.target.value)}
                  placeholder="Available courses, certifications, aircraft types..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-vertical"
                  rows={3}
                />
              </div>

              <div>
                <label htmlFor="otherCorrections" className="block text-sm font-medium text-gray-700 mb-1">
                  Other Corrections
                </label>
                <textarea
                  id="otherCorrections"
                  value={formData.otherCorrections}
                  onChange={(e) => handleInputChange('otherCorrections', e.target.value)}
                  placeholder="Any other information that needs updating..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-vertical"
                  rows={3}
                />
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            {onClose && (
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            )}

            <Button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Submit Feedback
                </>
              )}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
