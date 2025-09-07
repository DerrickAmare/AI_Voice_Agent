import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Phone, User, Upload, Clock, Shield, Send } from "lucide-react";

const formSchema = z.object({
  phoneNumber: z.string()
    .min(10, "Phone number must be at least 10 digits")
    .regex(/^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$/, "Please enter a valid phone number"),
  fullName: z.string().min(2, "Full name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email").optional().or(z.literal("")),
  callTime: z.enum(["immediate", "scheduled"]).default("immediate"),
});

type FormData = z.infer<typeof formSchema>;

interface PhoneFormProps {
  onSubmit: (requestId: string, phoneNumber: string) => void;
}

export function PhoneForm({ onSubmit }: PhoneFormProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const { toast } = useToast();

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      phoneNumber: "",
      fullName: "",
      email: "",
      callTime: "immediate",
    },
  });

  const submitMutation = useMutation({
    mutationFn: async (data: FormData & { resume?: File }) => {
      const formData = new FormData();
      formData.append("phoneNumber", data.phoneNumber);
      formData.append("fullName", data.fullName);
      if (data.email) formData.append("email", data.email);
      formData.append("callTime", data.callTime);
      if (data.resume) formData.append("resume", data.resume);

      const response = await fetch("/api/submit-request", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to submit request");
      }

      return response.json();
    },
    onSuccess: (data) => {
      toast({
        title: "Success!",
        description: "SMS confirmation sent. You'll receive a call in 5 minutes.",
      });
      onSubmit(data.requestId, form.getValues().phoneNumber);
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleFormSubmit = (data: FormData) => {
    submitMutation.mutate({ ...data, resume: selectedFile || undefined });
  };

  const formatPhoneNumber = (value: string) => {
    const digits = value.replace(/\D/g, "");
    if (digits.length >= 6) {
      return digits.replace(/(\d{3})(\d{3})(\d{4})/, "($1) $2-$3");
    } else if (digits.length >= 3) {
      return digits.replace(/(\d{3})(\d+)/, "($1) $2");
    }
    return digits;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        toast({
          title: "File too large",
          description: "Please select a file smaller than 10MB",
          variant: "destructive",
        });
        return;
      }
      setSelectedFile(file);
    }
  };

  return (
    <Card className="p-8">
      <CardContent>
        <h3 className="text-2xl font-bold text-foreground mb-6">Get Started - Submit Your Information!</h3>
        
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleFormSubmit)} className="space-y-6">
            {/* Phone Number Input */}
            <FormField
              control={form.control}
              name="phoneNumber"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center space-x-2">
                    <Phone className="w-4 h-4" />
                    <span>Your Phone Number</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      type="tel"
                      placeholder="(555) 123-4567"
                      className="text-lg font-mono"
                      onChange={(e) => {
                        const formatted = formatPhoneNumber(e.target.value);
                        field.onChange(formatted);
                      }}
                      data-testid="input-phone"
                    />
                  </FormControl>
                  <p className="text-sm text-muted-foreground">
                    We'll send you a confirmation and process your request
                  </p>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Name Input */}
            <FormField
              control={form.control}
              name="fullName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center space-x-2">
                    <User className="w-4 h-4" />
                    <span>Full Name</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="John Smith"
                      className="text-lg"
                      data-testid="input-name"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Email Input (Optional) */}
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email (Optional)</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      type="email"
                      placeholder="john@example.com"
                      data-testid="input-email"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Optional Resume Upload */}
            <div>
              <Label className="flex items-center space-x-2 mb-2">
                <Upload className="w-4 h-4" />
                <span>Current Resume (Optional)</span>
              </Label>
              <div 
                className="border-2 border-dashed border-border rounded-lg p-8 text-center bg-muted/50 cursor-pointer hover:border-primary hover:bg-primary/5 transition-colors"
                onClick={() => document.getElementById('resume-upload')?.click()}
                data-testid="file-drop-zone"
              >
                <div className="space-y-3">
                  <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                    <Upload className="text-primary w-6 h-6" />
                  </div>
                  <div>
                    {selectedFile ? (
                      <div>
                        <p className="text-foreground font-medium">{selectedFile.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    ) : (
                      <div>
                        <p className="text-foreground font-medium">Drop your resume here or click to browse</p>
                        <p className="text-sm text-muted-foreground">PDF, DOC, or DOCX up to 10MB</p>
                      </div>
                    )}
                  </div>
                </div>
                <input
                  id="resume-upload"
                  type="file"
                  className="hidden"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileChange}
                  data-testid="input-resume-file"
                />
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                If you have an existing resume, upload it and our AI will help improve it during the call.
              </p>
            </div>


            {/* Privacy Notice */}
            <div className="bg-muted p-4 rounded-lg">
              <div className="flex items-start space-x-3">
                <Shield className="text-green-600 w-5 h-5 mt-1 flex-shrink-0" />
                <div className="text-sm">
                  <p className="font-medium text-foreground">Your privacy is protected</p>
                  <p className="text-muted-foreground">We only use your information to create your resume. All data is encrypted and never shared with third parties.</p>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <Button 
              type="submit" 
              className="w-full text-lg py-6"
              disabled={submitMutation.isPending}
              data-testid="button-submit-request"
            >
              {submitMutation.isPending ? (
                <>
                  <Clock className="w-5 h-5 mr-2 animate-spin" />
                  Sending Request...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5 mr-2" />
                  Submit My Resume Request
                </>
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
