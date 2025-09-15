import { useState, useEffect } from "react";
import { RaceHeader } from "./RaceHeader";
import { HorseCard } from "./HorseCard";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CalendarDays, Filter, Zap, Loader2 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/components/ui/use-toast";

// Mock data - would be replaced with real API data
const mockRaces = [
  {
    id: 1,
    raceName: "Maiden Stakes",
    venue: "Churchill Downs",
    time: "2:30 PM EST",
    distance: "6f",
    surface: "Dirt",
    status: "upcoming" as const
  },
  {
    id: 2,
    raceName: "Derby Trial",
    venue: "Santa Anita",
    time: "4:15 PM EST",
    distance: "1m 1f",
    surface: "Turf",
    status: "upcoming" as const
  }
];

const mockHorses = [
  {
    position: 1,
    horseName: "Thunder Strike",
    jockey: "J. Rodriguez",
    trainer: "M. Johnson",
    odds: "3/1",
    confidence: 82,
    recentForm: ["1", "2", "1", "3", "1"],
    prediction: "favorite" as const,
    weight: "120 lbs",
    age: 4
  },
  {
    position: 2,
    horseName: "Desert Wind",
    jockey: "S. Martinez",
    trainer: "L. Thompson",
    odds: "5/1",
    confidence: 68,
    recentForm: ["2", "1", "4", "2", "1"],
    prediction: "value" as const,
    weight: "118 lbs",
    age: 3
  },
  {
    position: 3,
    horseName: "Midnight Runner",
    jockey: "K. Wilson",
    trainer: "D. Garcia",
    odds: "8/1",
    confidence: 45,
    recentForm: ["3", "5", "2", "1", "6"],
    prediction: "longshot" as const,
    weight: "122 lbs",
    age: 5
  },
  {
    position: 4,
    horseName: "Golden Arrow",
    jockey: "T. Davis",
    trainer: "R. Brown",
    odds: "12/1",
    confidence: 35,
    recentForm: ["4", "3", "7", "2", "4"],
    prediction: "longshot" as const,
    weight: "119 lbs",
    age: 4
  }
];

export const PredictionDashboard = () => {
  const [races, setRaces] = useState(mockRaces);
  const [horses, setHorses] = useState(mockHorses);
  const [selectedRace, setSelectedRace] = useState(mockRaces[0]);
  const [filterBy, setFilterBy] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchRacingData = async (endpoint = '/races/today') => {
    setLoading(true);
    setError(null);
    
    try {
      const { data, error: funcError } = await supabase.functions.invoke('fetch-racing-data', {
        body: { endpoint }
      });

      if (funcError) {
        throw new Error(funcError.message);
      }

      // For now, we'll use mock data but show that the API is connected
      console.log('Racing API response:', data);
      
      toast({
        title: "Racing API Connected",
        description: "Successfully fetched data using HTTP basic auth",
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch racing data';
      setError(errorMessage);
      console.error('Error fetching racing data:', err);
      
      toast({
        title: "API Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Fetch initial data on component mount
    fetchRacingData();
  }, []);

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              RacePredictor Pro
            </h1>
            <p className="text-muted-foreground mt-1">
              AI-powered horse racing predictions using real-time data
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Button variant="outline" className="border-racing-primary/50">
              <CalendarDays className="w-4 h-4 mr-2" />
              Today's Races
            </Button>
            <Button className="bg-gradient-primary hover:opacity-90">
              <Zap className="w-4 h-4 mr-2" />
              Live Updates
            </Button>
          </div>
        </div>

        {/* Race Selection */}
        <Card className="bg-racing-surface border-racing-surface p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h2 className="text-lg font-semibold text-foreground">Select Race:</h2>
               <Select value={selectedRace.id.toString()} onValueChange={(value) => {
                 const race = races.find(r => r.id.toString() === value);
                 if (race) setSelectedRace(race);
               }}>
                 <SelectTrigger className="w-80 bg-racing-surface-hover border-racing-primary/30">
                   <SelectValue />
                 </SelectTrigger>
                 <SelectContent>
                   {races.map((race) => (
                     <SelectItem key={race.id} value={race.id.toString()}>
                       {race.raceName} - {race.venue} ({race.time})
                     </SelectItem>
                   ))}
                 </SelectContent>
               </Select>
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <Select value={filterBy} onValueChange={setFilterBy}>
                <SelectTrigger className="w-40 bg-racing-surface-hover border-racing-primary/30">
                  <SelectValue placeholder="Filter by..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Horses</SelectItem>
                  <SelectItem value="favorites">Favorites</SelectItem>
                  <SelectItem value="value">Value Picks</SelectItem>
                  <SelectItem value="longshots">Longshots</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </Card>

        {/* Selected Race Header */}
        <RaceHeader {...selectedRace} />

        {/* Predictions Grid */}
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center">
            <Zap className="w-5 h-5 mr-2 text-racing-gold" />
            Race Predictions & Analysis
          </h2>
           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-2 gap-4">
             {loading ? (
               <div className="col-span-full flex items-center justify-center py-8">
                 <Loader2 className="w-6 h-6 animate-spin mr-2" />
                 <span>Loading racing data...</span>
               </div>
             ) : (
               horses
                 .filter(horse => filterBy === "all" || horse.prediction === filterBy)
                 .map((horse) => (
                   <HorseCard key={`${horse.horseName}-${horse.position}`} {...horse} />
                 ))
             )}
           </div>
        </div>

        {/* API Status */}
        <Card className="bg-racing-surface border-racing-gold/30 p-4">
          <div className="text-center">
            <p className="text-muted-foreground mb-3">
              <strong className="text-racing-gold">API Status:</strong> Connected to racing data service using HTTP basic authentication.
              {error && <span className="text-destructive"> Last error: {error}</span>}
            </p>
            <div className="flex items-center justify-center space-x-3">
              <Button 
                onClick={() => fetchRacingData()} 
                disabled={loading}
                variant="outline" 
                className="border-racing-gold text-racing-gold hover:bg-racing-gold hover:text-black"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Refreshing...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-2" />
                    Refresh Data
                  </>
                )}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};