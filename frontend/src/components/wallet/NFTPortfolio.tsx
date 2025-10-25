/*
 * NFT-Portfolio-Komponente für Wallet-Management
 */

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Image,
  Search,
  Filter,
  TrendingUp,
  Star,
  ExternalLink,
  RefreshCw,
  Eye,
  Heart,
  Share2
} from 'lucide-react'
import { useWallet } from '@/contexts/WalletContext'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

interface NFTItem {
  token_id: string
  contract_address: string
  chain: string
  name?: string
  description?: string
  image_url?: string
  attributes: Array<{ trait_type: string; value: string }>
  collection_name?: string
  rarity_score?: number
}

interface NFTCollection {
  name: string
  contract_address: string
  total_supply: number
  floor_price: number
  volume_traded: number
  owners: number
}

const NFTPortfolio: React.FC = () => {
  const { state } = useWallet()
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null)
  const [nfts, setNfts] = useState<NFTItem[]>([])
  const [collections, setCollections] = useState<NFTCollection[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [collectionFilter, setCollectionFilter] = useState('all')
  const [rarityFilter, setRarityFilter] = useState('all')

  const selectedWalletData = selectedWallet
    ? state.wallets.find(w => w.id === selectedWallet)
    : state.wallets[0]

  // Simulierte NFT-Daten für Demo
  useEffect(() => {
    if (selectedWalletData) {
      const demoNFTs: NFTItem[] = [
        {
          token_id: '1',
          contract_address: '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D',
          chain: 'ethereum',
          name: 'Bored Ape #1',
          description: 'A unique digital collectible',
          image_url: 'https://example.com/ape1.png',
          attributes: [
            { trait_type: 'Background', value: 'Blue' },
            { trait_type: 'Fur', value: 'Golden' },
            { trait_type: 'Eyes', value: 'Laser' }
          ],
          collection_name: 'Bored Ape Yacht Club',
          rarity_score: 0.85
        },
        {
          token_id: '2',
          contract_address: '0x60E4d786628Fea6478F785A6d7e704777c86a7c6',
          chain: 'ethereum',
          name: 'Mutant Ape #2',
          description: 'A mutated digital collectible',
          image_url: 'https://example.com/mutant2.png',
          attributes: [
            { trait_type: 'Background', value: 'Purple' },
            { trait_type: 'Fur', value: 'Robot' }
          ],
          collection_name: 'Mutant Ape Yacht Club',
          rarity_score: 0.72
        }
      ]

      setTimeout(() => {
        setNfts(demoNFTs)
      }, 1000)
    }
  }, [selectedWalletData])

  const filteredNFTs = nfts.filter(nft => {
    const matchesSearch = searchTerm === '' ||
      nft.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      nft.collection_name?.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesCollection = collectionFilter === 'all' ||
      nft.collection_name === collectionFilter

    const matchesRarity = rarityFilter === 'all' ||
      (rarityFilter === 'rare' && (nft.rarity_score || 0) > 0.7) ||
      (rarityFilter === 'common' && (nft.rarity_score || 0) <= 0.3)

    return matchesSearch && matchesCollection && matchesRarity
  })

  const getRarityBadge = (score?: number) => {
    if (!score) return null

    if (score >= 0.8) return <Badge variant="destructive">Legendary</Badge>
    if (score >= 0.6) return <Badge variant="warning">Rare</Badge>
    if (score >= 0.3) return <Badge variant="default">Uncommon</Badge>
    return <Badge variant="secondary">Common</Badge>
  }

  const formatValue = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'ETH',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4
    }).format(value)
  }

  if (!selectedWalletData) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">Wählen Sie eine Wallet aus, um NFTs anzuzeigen</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">NFT Portfolio</h2>
          <p className="text-muted-foreground">
            Verwalten Sie Ihre NFT-Sammlung für {selectedWalletData.address.slice(0, 10)}...
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedWallet || ''} onValueChange={setSelectedWallet}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Wallet auswählen" />
            </SelectTrigger>
            <SelectContent>
              {state.wallets.map(wallet => (
                <SelectItem key={wallet.id} value={wallet.id}>
                  {wallet.chain} - {wallet.address.slice(0, 10)}...
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Portfolio Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">NFTs</CardTitle>
            <Image className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{nfts.length}</div>
            <p className="text-xs text-muted-foreground">
              In Ihrer Sammlung
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Collections</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Set(nfts.map(nft => nft.collection_name)).size}
            </div>
            <p className="text-xs text-muted-foreground">
              Verschiedene Collections
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Portfolio-Wert</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatValue(nfts.reduce((sum, nft) => sum + (nft.rarity_score || 0) * 1, 0))}
            </div>
            <p className="text-xs text-muted-foreground">
              Geschätzter Wert
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rarity Score</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(nfts.reduce((sum, nft) => sum + (nft.rarity_score || 0), 0) / nfts.length * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Durchschnittliche Seltenheit
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filter und Suche
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="block text-sm font-medium mb-2">Suche</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="NFT Name, Collection..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Collection</label>
              <Select value={collectionFilter} onValueChange={setCollectionFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Alle Collections</SelectItem>
                  {Array.from(new Set(nfts.map(nft => nft.collection_name))).map(collection => (
                    <SelectItem key={collection} value={collection || ''}>
                      {collection}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Seltenheit</label>
              <Select value={rarityFilter} onValueChange={setRarityFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Alle</SelectItem>
                  <SelectItem value="common">Common</SelectItem>
                  <SelectItem value="rare">Rare+</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button variant="outline" onClick={() => {
                setSearchTerm('')
                setCollectionFilter('all')
                setRarityFilter('all')
              }}>
                Filter zurücksetzen
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* NFT Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filteredNFTs.map(nft => (
          <Card key={`${nft.contract_address}-${nft.token_id}`} className="overflow-hidden">
            <div className="aspect-square bg-gray-100 relative">
              {nft.image_url ? (
                <img
                  src={nft.image_url}
                  alt={nft.name || 'NFT'}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <Image className="h-12 w-12" />
                </div>
              )}

              {/* Rarity Badge */}
              <div className="absolute top-2 right-2">
                {getRarityBadge(nft.rarity_score)}
              </div>
            </div>

            <CardContent className="p-4">
              <div className="space-y-2">
                <div>
                  <h3 className="font-semibold text-sm truncate">
                    {nft.name || `Token #${nft.token_id}`}
                  </h3>
                  <p className="text-xs text-muted-foreground truncate">
                    {nft.collection_name}
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">
                    Rarity: {(nft.rarity_score || 0) * 100}%
                  </span>
                  <span className="text-xs font-medium">
                    {formatValue((nft.rarity_score || 0) * 1)}
                  </span>
                </div>

                {/* Attributes */}
                {nft.attributes && nft.attributes.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-xs font-medium">Attribute:</p>
                    <div className="flex flex-wrap gap-1">
                      {nft.attributes.slice(0, 3).map((attr, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {attr.value}
                        </Badge>
                      ))}
                      {nft.attributes.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{nft.attributes.length - 3}
                        </Badge>
                      )}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-1 pt-2">
                  <Button size="sm" variant="outline" className="flex-1">
                    <Eye className="h-3 w-3 mr-1" />
                    View
                  </Button>
                  <Button size="sm" variant="outline">
                    <Share2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredNFTs.length === 0 && !isLoading && (
        <div className="text-center py-8 text-muted-foreground">
          <Image className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Keine NFTs gefunden</p>
          <p className="text-sm">Versuchen Sie andere Filter oder fügen Sie NFTs zu Ihrer Sammlung hinzu</p>
        </div>
      )}

      {isLoading && (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      )}
    </div>
  )
}

export { NFTPortfolio }
