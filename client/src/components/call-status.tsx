import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ResumePreview } from "./resume-preview";
import { CheckCircle, Download, FileText, Mail, AlertTriangle, Clock } from "lucide-react";

interface CallStatusProps {
  requestId: string;
  phoneNumber: string;
  onViewDashboard: () => void;
}

export function CallStatus({ requestId, phoneNumber, onViewDashboard }: CallStatusProps) {
  const { data: requestStatus } = useQuery<any>({
    queryKey: ["/api/request-status", requestId],
    refetchInterval: 5000, // Check every 5 seconds
  });

  const handleDownloadPDF = async () => {
    try {
      const response = await fetch(`/api/download-resume/${requestId}`);
      if (!response.ok) throw new Error("Download failed");
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `resume-${requestId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Download error:", error);
      alert("Failed to download resume");
    }
  };

  if (requestStatus?.status === "completed" && requestStatus.resumeData) {
    return (
      <section className="mt-12" data-testid="resume-completed-section">
        <Card className="p-8">
          <CardContent>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-foreground">Your Resume is Ready!</h3>
              <span className="bg-green-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                <CheckCircle className="inline w-4 h-4 mr-1" />
                Completed
              </span>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8">
              {/* Resume Preview */}
              <div className="space-y-4">
                <h4 className="text-lg font-semibold text-foreground">Resume Preview</h4>
                <ResumePreview resumeData={requestStatus.resumeData} />
              </div>
              
              {/* Download Options */}
              <div className="space-y-4">
                <h4 className="text-lg font-semibold text-foreground">Download Options</h4>
                
                <div className="space-y-3">
                  <Button 
                    className="w-full"
                    onClick={handleDownloadPDF}
                    data-testid="button-download-pdf"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download PDF Resume
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="w-full"
                    data-testid="button-download-word"
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    Download Word Document
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="w-full"
                    data-testid="button-email-resume"
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    Email to Me
                  </Button>

                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={onViewDashboard}
                    data-testid="button-view-dashboard"
                  >
                    View All My Resumes
                  </Button>
                </div>
                
                <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
                  <h5 className="font-semibold text-green-800 mb-2">
                    <CheckCircle className="inline w-4 h-4 mr-2" />
                    Next Steps
                  </h5>
                  <ul className="text-sm text-green-700 space-y-1">
                    <li>• Customize your resume for each job application</li>
                    <li>• Add any recent achievements or certifications</li>
                    <li>• Use this as a starting point for future updates</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    );
  }

  if (requestStatus?.status === "failed") {
    return (
      <section className="mt-12" data-testid="request-failed-section">
        <Card className="p-8 border-red-200">
          <CardContent className="text-center max-w-2xl mx-auto">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="text-red-600 w-8 h-8" />
            </div>
            
            <h3 className="text-2xl font-bold text-foreground mb-2">Request Failed</h3>
            <p className="text-muted-foreground mb-6">
              We were unable to process your resume request. Please try again.
            </p>
            
            <div className="space-y-4">
              <Button 
                onClick={() => window.location.reload()}
                data-testid="button-try-again"
              >
                Try Again
              </Button>
              <Button 
                variant="outline"
                onClick={onViewDashboard}
                data-testid="button-view-dashboard-failed"
              >
                View Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>
    );
  }

  return (
    <section className="mt-12" data-testid="request-status-section">
      <Card className="p-8 bg-gradient-to-r from-green-50 via-blue-50 to-green-50 border-green-200">
        <CardContent className="text-center max-w-2xl mx-auto">
          <div className="relative mb-6">
            <div className="w-20 h-20 bg-green-600 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="text-white w-8 h-8" />
            </div>
            <div className="absolute inset-0 w-20 h-20 bg-green-600/20 rounded-full animate-ping mx-auto"></div>
          </div>
          
          <h3 className="text-2xl font-bold text-foreground mb-2">Request Submitted!</h3>
          <p className="text-muted-foreground mb-6">
            We've received your request for{" "}
            <span className="font-semibold text-foreground" data-testid="text-phone-number">
              {phoneNumber}
            </span>
            . Your resume will be processed and ready shortly.
          </p>
          
          <Card className="p-6 bg-white shadow-sm border border-border">
            <h4 className="font-semibold text-foreground mb-3">What's happening:</h4>
            <div className="space-y-2 text-sm text-muted-foreground text-left">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                <span>Processing your information</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                <span>Generating professional resume</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                <span>Preparing PDF for download</span>
              </div>
            </div>
          </Card>
          

          {requestStatus?.status === "in_call" && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-blue-800 font-semibold">
                <Clock className="inline w-4 h-4 mr-2 animate-spin" />
                Processing in progress! Your resume will be ready shortly.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
