"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";
import api from "@/lib/api";
import { getAuthHeaders } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
  X,
  List,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface WatchlistCompany {
  ticker: string;
  name?: string;
  sector?: string | null;
}

interface Watchlist {
  id: number;
  name: string;
  description?: string | null;
  companies?: WatchlistCompany[];
  created_at?: string;
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function WatchlistPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New watchlist form
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);

  // Expanded watchlist
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [expandedData, setExpandedData] = useState<Watchlist | null>(null);
  const [expandedLoading, setExpandedLoading] = useState(false);

  // Add ticker
  const [tickerInput, setTickerInput] = useState("");
  const [addingTicker, setAddingTicker] = useState(false);

  // -------------------------------------------------------------------------
  // Auth gate
  // -------------------------------------------------------------------------

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  // -------------------------------------------------------------------------
  // Fetch watchlists
  // -------------------------------------------------------------------------

  const fetchWatchlists = useCallback(async () => {
    try {
      setLoading(true);
      const { data } = await api.get<Watchlist[]>("/watchlists", {
        headers: getAuthHeaders(),
      });
      setWatchlists(data);
      setError(null);
    } catch {
      setError("Failed to load watchlists.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchWatchlists();
    }
  }, [isAuthenticated, fetchWatchlists]);

  // -------------------------------------------------------------------------
  // Create watchlist
  // -------------------------------------------------------------------------

  async function handleCreate() {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      await api.post("/watchlists", { name: newName.trim() }, { headers: getAuthHeaders() });
      setNewName("");
      await fetchWatchlists();
    } catch {
      setError("Failed to create watchlist.");
    } finally {
      setCreating(false);
    }
  }

  // -------------------------------------------------------------------------
  // Delete watchlist
  // -------------------------------------------------------------------------

  async function handleDelete(id: number) {
    try {
      await api.delete(`/watchlists/${id}`, { headers: getAuthHeaders() });
      if (expandedId === id) {
        setExpandedId(null);
        setExpandedData(null);
      }
      await fetchWatchlists();
    } catch {
      setError("Failed to delete watchlist.");
    }
  }

  // -------------------------------------------------------------------------
  // Expand / collapse
  // -------------------------------------------------------------------------

  async function toggleExpand(id: number) {
    if (expandedId === id) {
      setExpandedId(null);
      setExpandedData(null);
      return;
    }
    setExpandedId(id);
    setExpandedLoading(true);
    try {
      const { data } = await api.get<Watchlist>(`/watchlists/${id}`, {
        headers: getAuthHeaders(),
      });
      setExpandedData(data);
    } catch {
      setError("Failed to load watchlist details.");
    } finally {
      setExpandedLoading(false);
    }
  }

  // -------------------------------------------------------------------------
  // Add ticker
  // -------------------------------------------------------------------------

  async function handleAddTicker() {
    if (!tickerInput.trim() || !expandedId) return;
    setAddingTicker(true);
    try {
      await api.post(
        `/watchlists/${expandedId}/companies`,
        { ticker: tickerInput.trim().toUpperCase() },
        { headers: getAuthHeaders() },
      );
      setTickerInput("");
      // Refresh expanded watchlist
      const { data } = await api.get<Watchlist>(`/watchlists/${expandedId}`, {
        headers: getAuthHeaders(),
      });
      setExpandedData(data);
    } catch {
      setError("Failed to add ticker. Make sure it is a valid ticker symbol.");
    } finally {
      setAddingTicker(false);
    }
  }

  // -------------------------------------------------------------------------
  // Remove ticker
  // -------------------------------------------------------------------------

  async function handleRemoveTicker(ticker: string) {
    if (!expandedId) return;
    try {
      await api.delete(`/watchlists/${expandedId}/companies/${ticker}`, {
        headers: getAuthHeaders(),
      });
      const { data } = await api.get<Watchlist>(`/watchlists/${expandedId}`, {
        headers: getAuthHeaders(),
      });
      setExpandedData(data);
    } catch {
      setError("Failed to remove ticker.");
    }
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  if (authLoading || (!isAuthenticated && !authLoading)) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Watchlists</h1>
        <p className="text-muted-foreground">
          Create and manage your watchlists to track companies.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 underline hover:no-underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Create watchlist */}
      <Card>
        <CardContent className="flex items-center gap-3 pt-6">
          <Input
            placeholder="New watchlist name..."
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            className="max-w-sm"
          />
          <Button onClick={handleCreate} disabled={creating || !newName.trim()} size="sm">
            <Plus className="h-4 w-4" />
            {creating ? "Creating..." : "Create"}
          </Button>
        </CardContent>
      </Card>

      {/* Watchlist list */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <p className="text-muted-foreground">Loading watchlists...</p>
        </div>
      ) : watchlists.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <List className="h-10 w-10 text-muted-foreground/50 mb-3" />
            <p className="text-muted-foreground">
              No watchlists yet. Create one above to get started.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {watchlists.map((wl) => {
            const isExpanded = expandedId === wl.id;
            return (
              <Card key={wl.id}>
                <CardHeader className="flex flex-row items-center justify-between py-4">
                  <button
                    onClick={() => toggleExpand(wl.id)}
                    className="flex items-center gap-2 text-left"
                  >
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    )}
                    <div>
                      <CardTitle className="text-base">{wl.name}</CardTitle>
                      {wl.description && (
                        <CardDescription className="mt-0.5">
                          {wl.description}
                        </CardDescription>
                      )}
                    </div>
                  </button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(wl.id)}
                    className="text-muted-foreground hover:text-destructive shrink-0"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </CardHeader>

                {isExpanded && (
                  <>
                    <Separator />
                    <CardContent className="pt-4 space-y-4">
                      {expandedLoading ? (
                        <p className="text-sm text-muted-foreground">Loading...</p>
                      ) : (
                        <>
                          {/* Add ticker */}
                          <div className="flex items-center gap-2">
                            <Input
                              placeholder="Add ticker (e.g. AAPL)..."
                              value={tickerInput}
                              onChange={(e) => setTickerInput(e.target.value)}
                              onKeyDown={(e) => e.key === "Enter" && handleAddTicker()}
                              className="max-w-xs"
                            />
                            <Button
                              size="sm"
                              onClick={handleAddTicker}
                              disabled={addingTicker || !tickerInput.trim()}
                            >
                              <Plus className="h-4 w-4" />
                              {addingTicker ? "Adding..." : "Add"}
                            </Button>
                          </div>

                          {/* Companies */}
                          {expandedData?.companies &&
                          expandedData.companies.length > 0 ? (
                            <div className="divide-y divide-border rounded-md border">
                              {expandedData.companies.map((c) => (
                                <div
                                  key={c.ticker}
                                  className="flex items-center justify-between px-4 py-2.5"
                                >
                                  <div className="flex items-center gap-3">
                                    <span className="font-mono text-sm font-semibold">
                                      {c.ticker}
                                    </span>
                                    {c.name && (
                                      <span className="text-sm text-muted-foreground">
                                        {c.name}
                                      </span>
                                    )}
                                    {c.sector && (
                                      <span className="text-xs text-muted-foreground/70">
                                        {c.sector}
                                      </span>
                                    )}
                                  </div>
                                  <button
                                    onClick={() => handleRemoveTicker(c.ticker)}
                                    className="text-muted-foreground hover:text-destructive transition-colors"
                                  >
                                    <X className="h-4 w-4" />
                                  </button>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground">
                              No companies in this watchlist yet.
                            </p>
                          )}
                        </>
                      )}
                    </CardContent>
                  </>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
