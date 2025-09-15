import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock, MapPin, Trophy } from "lucide-react";

interface RaceHeaderProps {
  raceName: string;
  venue: string;
  time: string;
  distance: string;
  surface: string;
  status: "upcoming" | "live" | "finished";
}

export const RaceHeader = ({ raceName, venue, time, distance, surface, status }: RaceHeaderProps) => {
  return (
    <Card className="bg-gradient-surface border-racing-surface hover:border-racing-primary/30 transition-all duration-300">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-foreground mb-2">{raceName}</h2>
            <div className="flex items-center space-x-4 text-muted-foreground">
              <div className="flex items-center space-x-1">
                <MapPin className="w-4 h-4" />
                <span>{venue}</span>
              </div>
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4" />
                <span>{time}</span>
              </div>
              <div className="flex items-center space-x-1">
                <Trophy className="w-4 h-4" />
                <span>{distance} • {surface}</span>
              </div>
            </div>
          </div>
          <Badge 
            variant={status === "live" ? "destructive" : status === "upcoming" ? "default" : "secondary"}
            className={status === "live" ? "bg-red-600 animate-pulse" : status === "upcoming" ? "bg-racing-gold text-racing-gold-foreground" : ""}
          >
            {status.toUpperCase()}
          </Badge>
        </div>
      </div>
    </Card>
  );
};