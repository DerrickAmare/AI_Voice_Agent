import { useState } from "react";
import { useLocation } from "wouter";
import { PhoneForm } from "@/components/phone-form";
import { CallStatus } from "@/components/call-status";
import { Card, CardContent } from "@/components/ui/card";
import { Phone, Clock, Download, Shield, CheckCircle, Lightbulb, MessageCircle, TrendingUp } from "lucide-react";

export default function Home() {
  const [, setLocation] = useLocation();
  const [requestId, setRequestId] = useState<string | null>(null);
  const [submittedPhone, setSubmittedPhone] = useState<string>("");

  const handleFormSubmit = (id: string, phone: string) => {
    setRequestId(id);
    setSubmittedPhone(phone);
  };

  const handleViewDashboard = () => {
    setLocation(`/dashboard?phone=${encodeURIComponent(submittedPhone)}`);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border shadow-sm sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <Phone className="text-primary-foreground w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">AI Resume Builder</h1>
                <p className="text-sm text-muted-foreground">Build your resume over the phone</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-green-600">
              <Shield className="w-4 h-4" />
              <span className="text-sm font-medium">Secure & Private</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <section className="text-center mb-12">
          <Card className="p-8 mb-8">
            <CardContent className="max-w-2xl mx-auto">
              <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
                Build Your Professional Resume
              </h2>
              <p className="text-lg text-muted-foreground mb-6">
                Create a polished resume by submitting your information through our simple form. Perfect for integrating with your existing workflow.
              </p>
              <div className="flex flex-wrap justify-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-green-600" />
                  <span>5-10 minutes</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Phone className="w-4 h-4 text-green-600" />
                  <span>API integration</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Download className="w-4 h-4 text-green-600" />
                  <span>Instant PDF</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Progress Steps */}
        <section className="mb-8">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0 md:space-x-4">
            <div className={`flex items-center space-x-3 px-4 py-3 rounded-lg shadow-sm ${!requestId ? 'bg-primary text-primary-foreground' : 'bg-green-600 text-white'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${!requestId ? 'bg-primary-foreground text-primary' : 'bg-white text-green-600'}`}>1</div>
              <span className="font-medium">Submit Phone Number</span>
            </div>
            <div className="hidden md:block flex-1 h-px bg-border"></div>
            <div className={`flex items-center space-x-3 px-4 py-3 rounded-lg ${requestId ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${requestId ? 'bg-white text-green-600' : 'bg-muted-foreground text-muted'}`}>2</div>
              <span className="font-medium">Receive SMS Confirmation</span>
            </div>
            <div className="hidden md:block flex-1 h-px bg-border"></div>
            <div className="flex items-center space-x-3 bg-muted text-muted-foreground px-4 py-3 rounded-lg">
              <div className="w-8 h-8 bg-muted-foreground text-muted rounded-full flex items-center justify-center font-bold">3</div>
              <span className="font-medium">AI Voice Interview</span>
            </div>
            <div className="hidden md:block flex-1 h-px bg-border"></div>
            <div className="flex items-center space-x-3 bg-muted text-muted-foreground px-4 py-3 rounded-lg">
              <div className="w-8 h-8 bg-muted-foreground text-muted rounded-full flex items-center justify-center font-bold">4</div>
              <span className="font-medium">Download Resume</span>
            </div>
          </div>
        </section>

        {/* Show either form or confirmation */}
        {!requestId ? (
          <div className="grid md:grid-cols-3 gap-8">
            {/* Main Form Section */}
            <div className="md:col-span-2">
              <PhoneForm onSubmit={handleFormSubmit} />
            </div>

            {/* Sidebar Information */}
            <div className="space-y-6">
              {/* What to Expect */}
              <Card className="p-6">
                <h4 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                  <Lightbulb className="text-yellow-500 w-5 h-5 mr-2" />
                  What to Expect
                </h4>
                <div className="space-y-3 text-sm">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <CheckCircle className="text-green-600 w-3 h-3" />
                    </div>
                    <p className="text-muted-foreground">Submit your information through our simple form</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <CheckCircle className="text-green-600 w-3 h-3" />
                    </div>
                    <p className="text-muted-foreground">Your request will be processed automatically</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <CheckCircle className="text-green-600 w-3 h-3" />
                    </div>
                    <p className="text-muted-foreground">Professional resume generated quickly</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <CheckCircle className="text-green-600 w-3 h-3" />
                    </div>
                    <p className="text-muted-foreground">Download your resume in PDF format</p>
                  </div>
                </div>
              </Card>

              {/* Success Statistics */}
              <Card className="p-6 bg-gradient-to-br from-green-50 to-blue-50 border-green-200">
                <h4 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                  <TrendingUp className="text-green-600 w-5 h-5 mr-2" />
                  Success Stories
                </h4>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600">89%</div>
                    <div className="text-xs text-muted-foreground">Get job interviews</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">4.8★</div>
                    <div className="text-xs text-muted-foreground">User satisfaction</div>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        ) : (
          <CallStatus 
            requestId={requestId} 
            phoneNumber={submittedPhone}
            onViewDashboard={handleViewDashboard}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-muted border-t border-border mt-16">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <h5 className="font-semibold text-foreground mb-3">AI Resume Builder</h5>
              <p className="text-sm text-muted-foreground">Helping workers build professional resumes through simple phone conversations.</p>
            </div>
            <div>
              <h5 className="font-semibold text-foreground mb-3">Support</h5>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p><Phone className="inline w-4 h-4 mr-2" />(555) 123-HELP</p>
                <p><MessageCircle className="inline w-4 h-4 mr-2" />support@airesume.com</p>
              </div>
            </div>
            <div>
              <h5 className="font-semibold text-foreground mb-3">Privacy & Security</h5>
              <div className="space-y-2 text-sm">
                <a href="#" className="text-muted-foreground hover:text-primary block">Privacy Policy</a>
                <a href="#" className="text-muted-foreground hover:text-primary block">Terms of Service</a>
              </div>
            </div>
          </div>
          <div className="border-t border-border mt-8 pt-6 text-center">
            <p className="text-sm text-muted-foreground">© 2025 AI Resume Builder. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
