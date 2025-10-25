/*
 * Guided Tours Komponente für Blockchain-Forensik-Anwendung
 * Implementiert interaktive Touren mit react-joyride
 */

import React, { useState, useEffect, useCallback, ReactNode } from 'react'
import Joyride, { CallBackProps, STATUS, Step, EVENTS, Props as JoyrideProps } from 'react-joyride'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Play,
  SkipForward,
  CheckCircle,
  BookOpen,
  BarChart3,
  Users,
  Settings,
  HelpCircle
} from 'lucide-react'
import { useI18n } from '@/contexts/I18nContext'

interface TourStep {
  step_id: string
  title: string
  content: string
  target: string
  placement: string
  disable_beacon?: boolean
  show_skip_button?: boolean
  spotlight_clicks?: boolean
}

interface Tour {
  tour_id: string
  name: string
  description: string
  type: string
  step_count: number
  status: string
  progress: number
  is_completed: boolean
}

interface TourProgress {
  tour_id: string
  current_step: number
  status: string
  started_at?: string
  completed_at?: string
  step_times?: Record<number, number>
}

interface TourManagerProps {
  children: ReactNode
  currentPage?: string
}

const TourManager: React.FC<TourManagerProps> = ({ children, currentPage }) => {
  const { t } = useI18n()
  const [availableTours, setAvailableTours] = useState<Tour[]>([])
  const [activeTour, setActiveTour] = useState<Tour | null>(null)
  const [tourSteps, setTourSteps] = useState<Step[]>([])
  const [tourProgress, setTourProgress] = useState<TourProgress | null>(null)
  const [isTourRunning, setIsTourRunning] = useState(false)
  const [showTourSelector, setShowTourSelector] = useState(false)

  // Tour-Daten laden
  useEffect(() => {
    const loadTours = async () => {
      try {
        const response = await fetch('/api/v1/tours/available')
        if (response.ok) {
          const tours: Tour[] = await response.json()
          setAvailableTours(tours)
        }
      } catch (error) {
        console.error('Fehler beim Laden der Touren:', error)
      }
    }

    loadTours()
  }, [])

  // Tour starten
  const startTour = useCallback(async (tour: Tour) => {
    try {
      // Tour-Details laden
      const response = await fetch(`/api/v1/tours/${tour.tour_id}`)
      if (!response.ok) {
        throw new Error('Tour nicht gefunden')
      }

      const tourData = await response.json()

      // Tour starten
      const startResponse = await fetch(`/api/v1/tours/${tour.tour_id}/start`, {
        method: 'POST'
      })

      if (!startResponse.ok) {
        throw new Error('Tour konnte nicht gestartet werden')
      }

      // Steps für react-joyride vorbereiten
      const steps: Step[] = tourData.steps.map((step: TourStep) => ({
        target: step.target,
        title: step.title,
        content: step.content,
        placement: step.placement as any,
        disableBeacon: step.disable_beacon,
        showSkipButton: step.show_skip_button,
        spotlightClicks: step.spotlight_clicks
      }))

      setActiveTour(tour)
      setTourSteps(steps)
      setIsTourRunning(true)
      setShowTourSelector(false)

    } catch (error) {
      console.error('Fehler beim Starten der Tour:', error)
      // Toast notification würde hier stehen
    }
  }, [])

  // Tour-Fortschritt aktualisieren
  const updateTourProgress = useCallback(async (stepIndex: number, action: string) => {
    if (!activeTour) return

    try {
      await fetch('/api/v1/tours/progress', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tour_id: activeTour.tour_id,
          step_index: stepIndex,
          action: action
        })
      })

      // Fortschritt aktualisieren
      setTourProgress(prev => prev ? {
        ...prev,
        current_step: stepIndex
      } : null)

    } catch (error) {
      console.error('Fehler beim Aktualisieren des Tour-Fortschritts:', error)
    }
  }, [activeTour])

  // Tour überspringen
  const skipTour = useCallback(async () => {
    if (!activeTour) return

    try {
      await fetch(`/api/v1/tours/${activeTour.tour_id}/skip`, {
        method: 'POST'
      })

      setIsTourRunning(false)
      setActiveTour(null)
      setTourSteps([])
      setTourProgress(null)

    } catch (error) {
      console.error('Fehler beim Überspringen der Tour:', error)
    }
  }, [activeTour])

  // Joyride Callbacks
  const handleJoyrideCallback = useCallback((data: CallBackProps) => {
    const { action, index, status, type } = data

    if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
      // Tour beendet
      setIsTourRunning(false)
      setActiveTour(null)
      setTourSteps([])
      setTourProgress(null)
      return
    }

    if (type === EVENTS.STEP_AFTER) {
      // Nächster Schritt
      updateTourProgress(index + 1, 'next')
    }

    if (type === EVENTS.TARGET_NOT_FOUND) {
      // Target nicht gefunden - Schritt überspringen
      console.warn(`Tour target nicht gefunden: ${tourSteps[index]?.target}`)
    }
  }, [updateTourProgress, tourSteps])

  // Tour-Button in UI integrieren
  const TourButton = () => (
    <Button
      variant="outline"
      size="sm"
      onClick={() => setShowTourSelector(!showTourSelector)}
      className="relative"
    >
      <HelpCircle className="h-4 w-4 mr-2" />
      {t('tours.start_tour')}
      {availableTours.filter(tour => !tour.is_completed).length > 0 && (
        <Badge variant="secondary" className="ml-2 text-xs">
          {availableTours.filter(tour => !tour.is_completed).length}
        </Badge>
      )}
    </Button>
  )

  // Tour-Auswahl Modal
  const TourSelector = () => {
    if (!showTourSelector) return null

    const availableToursForPage = availableTours.filter(tour =>
      !tour.is_completed &&
      (tour.tour_id.includes(currentPage || '') || tour.tour_id === 'onboarding_main')
    )

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <Card className="w-full max-w-md mx-4">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              {t('tours.available_tours')}
            </CardTitle>
            <CardDescription>
              {t('tours.select_tour_description')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {availableToursForPage.length === 0 ? (
              <p className="text-center text-muted-foreground py-4">
                {t('tours.no_tours_available')}
              </p>
            ) : (
              availableToursForPage.map(tour => (
                <div
                  key={tour.tour_id}
                  className="border rounded-lg p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => startTour(tour)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{tour.name}</h4>
                    <Badge variant={tour.status === 'not_started' ? 'secondary' : 'outline'}>
                      {tour.step_count} {t('tours.steps')}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {tour.description}
                  </p>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {tour.type.replace('_', ' ').toUpperCase()}
                    </Badge>
                    {tour.progress > 0 && (
                      <span className="text-xs text-muted-foreground">
                        {tour.progress}/{tour.step_count} {t('tours.completed')}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setShowTourSelector(false)}>
                {t('common.close')}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Tour-Overlay während der Tour
  const TourOverlay = () => {
    if (!isTourRunning || !activeTour) return null

    // Typ-sicherer Wrapper für react-joyride, um JSX-Kompatibilitätsfehler zu vermeiden
    const JoyrideComponent = Joyride as unknown as React.ComponentType<JoyrideProps>

    return (
      <>
        {/* Tour Progress Indicator */}
        <div className="fixed top-4 right-4 z-40">
          <Card className="w-64">
            <CardContent className="p-3">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-sm">{activeTour.name}</h4>
                <Button variant="ghost" size="sm" onClick={skipTour}>
                  <SkipForward className="h-4 w-4" />
                </Button>
              </div>
              <div className="w-full bg-muted rounded-full h-2 mb-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${((tourProgress?.current_step || 0) / tourSteps.length) * 100}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {t('tours.step')} {tourProgress?.current_step || 0} {t('tours.of')} {tourSteps.length}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Joyride Tour */}
        <JoyrideComponent
          steps={tourSteps}
          run={isTourRunning}
          callback={handleJoyrideCallback}
          continuous={true}
          showProgress={true}
          showSkipButton={true}
          disableOverlayClose={true}
          disableCloseOnEsc={true}
          locale={{
            back: t('common.back'),
            close: t('common.close'),
            last: t('tours.finish'),
            next: t('common.next'),
            open: t('tours.start'),
            skip: t('tours.skip')
          }}
          styles={{
            options: {
              primaryColor: 'hsl(var(--primary))',
              textColor: 'hsl(var(--foreground))',
              backgroundColor: 'hsl(var(--background))',
              overlayColor: 'rgba(0, 0, 0, 0.5)',
              spotlightShadow: '0 0 15px rgba(0, 0, 0, 0.5)',
              beaconSize: 36,
              zIndex: 100,
            },
            tooltip: {
              borderRadius: 8,
              fontSize: 14,
            },
            tooltipContainer: {
              textAlign: 'left',
            },
            buttonNext: {
              backgroundColor: 'hsl(var(--primary))',
              fontSize: 14,
            },
            buttonBack: {
              color: 'hsl(var(--muted-foreground))',
              marginRight: 8,
            },
            buttonSkip: {
              color: 'hsl(var(--muted-foreground))',
            },
            buttonClose: {
              height: 14,
              width: 14,
            }
          }}
        />
      </>
    )
  }

  return (
    <>
      <TourButton />
      <TourSelector />
      <TourOverlay />
      {children}
    </>
  )
}

export { TourManager }

// Hook für Tour-Management
export const useTours = () => {
  const [tours, setTours] = useState<Tour[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const loadTours = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/v1/tours/available')
      if (response.ok) {
        const toursData: Tour[] = await response.json()
        setTours(toursData)
      }
    } catch (error) {
      console.error('Fehler beim Laden der Touren:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const startTour = useCallback(async (tourId: string) => {
    try {
      const response = await fetch(`/api/v1/tours/${tourId}/start`, {
        method: 'POST'
      })
      return response.ok
    } catch (error) {
      console.error('Fehler beim Starten der Tour:', error)
      return false
    }
  }, [])

  useEffect(() => {
    loadTours()
  }, [loadTours])

  return {
    tours,
    isLoading,
    loadTours,
    startTour
  }
}
