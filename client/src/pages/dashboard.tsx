import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ResumePreview } from "@/components/resume-preview";
import { Download, FileText, Mail, ArrowLeft, Clock, CheckCircle, XCircle } from "lucide-react";

interface ResumeRequest {
  id: string;
  status: string;
  scheduledCallTime: string;
  resumeData: any;
  generatedResuePdfUrl: string;
  completedAt: string;
}

export default function Dashboard() {
  const [, setLocation] = useLocation();
  const [phoneNumber, setPhoneNumber] = useState<string>("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const phone = params.get("phone");
    if (phone) {
      setPhoneNumber(phone);
    } else {
      setLocation("/");
    }
  }, [setLocation]);

  const { data: userRequests, isLoading } = useQuery<{requests: ResumeRequest[]}>({
    queryKey: ["/api/user", phoneNumber, "requests"],
    enabled: !!phoneNumber,
  });

  const handleDownloadPDF = async (requestId: string) => {
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-red-600" />;
      case "in_call":
        return <Clock className="w-5 h-5 text-blue-600 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-600" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "pending":
        return "Pending";
      case "sms_sent":
        return "SMS Sent";
      case "in_call":
        return "In Progress";
      case "completed":
        return "Completed";
      case "failed":
        return "Failed";
      default:
        return status;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Clock className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading your resumes...</p>
        </div>
      </div>
    );
  }

  const requests: ResumeRequest[] = userRequests?.requests || [];
  const completedRequests = requests.filter(r => r.status === "completed");

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setLocation("/")}
                data-testid="button-back-home"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Home
              </Button>
              <div>
                <h1 className="text-xl font-bold text-foreground">Resume Dashboard</h1>
                <p className="text-sm text-muted-foreground">Phone: {phoneNumber}</p>
              </div>
            </div>
            <Button 
              onClick={() => setLocation("/")}
              data-testid="button-create-new"
            >
              Create New Resume
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {requests.length === 0 ? (
          <Card className="p-8 text-center">
            <CardContent>
              <FileText className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-xl font-semibold text-foreground mb-2">No Resumes Yet</h3>
              <p className="text-muted-foreground mb-4">
                You haven't created any resumes yet. Start by submitting your phone number for an AI interview.
              </p>
              <Button onClick={() => setLocation("/")} data-testid="button-get-started">
                Get Started
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-8">
            {/* Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Resume Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">{requests.length}</div>
                    <div className="text-sm text-muted-foreground">Total Requests</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{completedRequests.length}</div>
                    <div className="text-sm text-muted-foreground">Completed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">{requests.filter(r => r.status === "in_call").length}</div>
                    <div className="text-sm text-muted-foreground">In Progress</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{requests.filter(r => r.status === "failed").length}</div>
                    <div className="text-sm text-muted-foreground">Failed</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Resume Requests */}
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-foreground">Your Resume Requests</h2>
              
              {requests.map((request) => (
                <Card key={request.id} className={request.status === "completed" ? "border-green-200" : ""}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(request.status)}
                        <div>
                          <CardTitle className="text-lg">Resume Request</CardTitle>
                          <p className="text-sm text-muted-foreground">
                            Created: {new Date(request.scheduledCallTime).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          request.status === "completed" 
                            ? "bg-green-100 text-green-800" 
                            : request.status === "failed"
                            ? "bg-red-100 text-red-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}>
                          {getStatusText(request.status)}
                        </span>
                      </div>
                    </div>
                  </CardHeader>
                  
                  {request.status === "completed" && request.resumeData && (
                    <CardContent>
                      <div className="grid md:grid-cols-2 gap-8">
                        {/* Resume Preview */}
                        <div>
                          <h4 className="text-lg font-semibold text-foreground mb-4">Resume Preview</h4>
                          <ResumePreview resumeData={request.resumeData} />
                        </div>
                        
                        {/* Download Options */}
                        <div className="space-y-4">
                          <h4 className="text-lg font-semibold text-foreground">Download Options</h4>
                          
                          <div className="space-y-3">
                            <Button 
                              className="w-full" 
                              onClick={() => handleDownloadPDF(request.id)}
                              data-testid={`button-download-pdf-${request.id}`}
                            >
                              <Download className="w-4 h-4 mr-2" />
                              Download PDF Resume
                            </Button>
                            
                            <Button 
                              variant="outline" 
                              className="w-full"
                              data-testid={`button-download-word-${request.id}`}
                            >
                              <FileText className="w-4 h-4 mr-2" />
                              Download Word Document
                            </Button>
                            
                            <Button 
                              variant="outline" 
                              className="w-full"
                              data-testid={`button-email-resume-${request.id}`}
                            >
                              <Mail className="w-4 h-4 mr-2" />
                              Email to Me
                            </Button>
                          </div>
                          
                          {request.completedAt && (
                            <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
                              <h5 className="font-semibold text-green-800 mb-2">
                                Resume Completed!
                              </h5>
                              <p className="text-sm text-green-700">
                                Completed on {new Date(request.completedAt).toLocaleString()}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  )}
                  
                  {request.status === "failed" && (
                    <CardContent>
                      <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                        <p className="text-red-800">
                          This resume request failed to complete. Please try creating a new one.
                        </p>
                      </div>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
