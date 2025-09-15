import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TrendingUp, TrendingDown, Star } from "lucide-react";

interface HorseCardProps {
  position: number;
  horseName: string;
  jockey: string;
  trainer: string;
  odds: string;
  confidence: number;
  recentForm: string[];
  prediction: "favorite" | "value" | "longshot";
  weight: string;
  age: number;
}

export const HorseCard = ({
  position,
  horseName,
  jockey,
  trainer,
  odds,
  confidence,
  recentForm,
  prediction,
  weight,
  age
}: HorseCardProps) => {
  const getPredictionColor = (pred: string) => {
    switch (pred) {
      case "favorite": return "bg-racing-gold text-black";
      case "value": return "bg-racing-primary text-white";
      case "longshot": return "bg-secondary text-secondary-foreground";
      default: return "bg-muted text-muted-foreground";
    }
  };

  const getConfidenceIcon = () => {
    if (confidence >= 75) return <TrendingUp className="w-4 h-4 text-racing-gold" />;
    if (confidence >= 50) return <Star className="w-4 h-4 text-racing-primary" />;
    return <TrendingDown className="w-4 h-4 text-muted-foreground" />;
  };

  return (
    <Card className="bg-racing-surface border-racing-surface hover:border-racing-primary/50 hover:shadow-racing transition-all duration-300 group">
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-racing-primary rounded-full flex items-center justify-center text-sm font-bold text-white">
              {position}
            </div>
            <div>
              <h3 className="font-semibold text-foreground group-hover:text-racing-gold transition-colors">
                {horseName}
              </h3>
              <p className="text-sm text-muted-foreground">{age}y • {weight}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold text-racing-gold">{odds}</div>
            <Badge className={getPredictionColor(prediction)} variant="secondary">
              {prediction}
            </Badge>
          </div>
        </div>

        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Jockey:</span>
            <span className="text-foreground">{jockey}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Trainer:</span>
            <span className="text-foreground">{trainer}</span>
          </div>
        </div>

        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Confidence</span>
            <div className="flex items-center space-x-1">
              {getConfidenceIcon()}
              <span className="text-sm font-semibold">{confidence}%</span>
            </div>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div 
              className="h-2 rounded-full bg-gradient-primary transition-all duration-500"
              style={{ width: `${confidence}%` }}
            />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex space-x-1">
            <span className="text-xs text-muted-foreground">Form:</span>
            {recentForm.map((result, index) => (
              <span 
                key={index}
                className={`text-xs px-1 rounded ${
                  result === "1" ? "bg-racing-gold text-black" :
                  result === "2" ? "bg-racing-primary text-white" :
                  result === "3" ? "bg-accent text-accent-foreground" :
                  "bg-muted text-muted-foreground"
                }`}
              >
                {result}
              </span>
            ))}
          </div>
          <Button variant="outline" size="sm" className="border-racing-primary/50 hover:bg-racing-primary hover:text-white">
            Details
          </Button>
        </div>
      </div>
    </Card>
  );
};