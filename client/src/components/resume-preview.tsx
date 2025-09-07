import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ResumeData {
  personalInfo: {
    fullName: string;
    phoneNumber: string;
    email?: string;
    address?: string;
  };
  summary: string;
  workExperience: Array<{
    jobTitle: string;
    company: string;
    duration: string;
    responsibilities: string[];
    achievements?: string[];
  }>;
  skills: string[];
  education: Array<{
    degree?: string;
    school?: string;
    year?: string;
    certification?: string;
  }>;
  additionalInfo?: {
    certifications?: string[];
    languages?: string[];
    references?: string;
  };
}

interface ResumePreviewProps {
  resumeData: ResumeData;
}

export function ResumePreview({ resumeData }: ResumePreviewProps) {
  return (
    <Card className="bg-white border border-gray-200">
      <CardContent className="p-6 space-y-4 text-sm">
        {/* Header */}
        <div className="border-b border-gray-200 pb-3">
          <h5 className="font-bold text-foreground text-lg" data-testid="text-resume-name">
            {resumeData.personalInfo.fullName}
          </h5>
          <div className="text-muted-foreground space-y-1">
            <p data-testid="text-resume-phone">{resumeData.personalInfo.phoneNumber}</p>
            {resumeData.personalInfo.email && (
              <p data-testid="text-resume-email">{resumeData.personalInfo.email}</p>
            )}
            {resumeData.personalInfo.address && (
              <p data-testid="text-resume-address">{resumeData.personalInfo.address}</p>
            )}
          </div>
        </div>
        
        {/* Professional Summary */}
        {resumeData.summary && (
          <div>
            <h6 className="font-semibold text-foreground mb-2">Professional Summary</h6>
            <p className="text-muted-foreground" data-testid="text-resume-summary">
              {resumeData.summary}
            </p>
          </div>
        )}
        
        {/* Work Experience */}
        {resumeData.workExperience.length > 0 && (
          <div>
            <h6 className="font-semibold text-foreground mb-2">Work Experience</h6>
            <div className="space-y-3">
              {resumeData.workExperience.map((job, index) => (
                <div key={index} data-testid={`work-experience-${index}`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-foreground">{job.jobTitle}</p>
                      <p className="text-muted-foreground">{job.company}</p>
                    </div>
                    <p className="text-sm text-muted-foreground">{job.duration}</p>
                  </div>
                  {job.responsibilities.length > 0 && (
                    <ul className="mt-1 text-muted-foreground text-xs space-y-1">
                      {job.responsibilities.map((resp, idx) => (
                        <li key={idx}>• {resp}</li>
                      ))}
                    </ul>
                  )}
                  {job.achievements && job.achievements.length > 0 && (
                    <ul className="mt-1 text-muted-foreground text-xs space-y-1">
                      {job.achievements.map((achievement, idx) => (
                        <li key={idx}>• {achievement}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Skills */}
        {resumeData.skills.length > 0 && (
          <div>
            <h6 className="font-semibold text-foreground mb-2">Key Skills</h6>
            <div className="flex flex-wrap gap-1" data-testid="skills-container">
              {resumeData.skills.map((skill, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Education */}
        {resumeData.education.length > 0 && (
          <div>
            <h6 className="font-semibold text-foreground mb-2">Education</h6>
            <div className="space-y-2">
              {resumeData.education.map((edu, index) => (
                <div key={index} data-testid={`education-${index}`}>
                  {edu.degree && edu.school ? (
                    <p className="text-muted-foreground">
                      {edu.degree} - {edu.school}
                      {edu.year && ` (${edu.year})`}
                    </p>
                  ) : edu.certification ? (
                    <p className="text-muted-foreground">{edu.certification}</p>
                  ) : (
                    <p className="text-muted-foreground">
                      {edu.school || "Education"}
                      {edu.year && ` (${edu.year})`}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Additional Information */}
        {resumeData.additionalInfo && (
          <>
            {resumeData.additionalInfo.certifications && resumeData.additionalInfo.certifications.length > 0 && (
              <div>
                <h6 className="font-semibold text-foreground mb-2">Certifications</h6>
                <ul className="text-muted-foreground space-y-1">
                  {resumeData.additionalInfo.certifications.map((cert, index) => (
                    <li key={index}>• {cert}</li>
                  ))}
                </ul>
              </div>
            )}

            {resumeData.additionalInfo.languages && resumeData.additionalInfo.languages.length > 0 && (
              <div>
                <h6 className="font-semibold text-foreground mb-2">Languages</h6>
                <p className="text-muted-foreground">
                  {resumeData.additionalInfo.languages.join(", ")}
                </p>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
