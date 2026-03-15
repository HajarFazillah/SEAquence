import React from 'react';
import {
  Home,
  User,
  Users,
  MessageCircle,
  Mic,
  Settings,
  Bell,
  Search,
  ChevronLeft,
  ChevronRight,
  ArrowRight,
  ArrowLeft,
  X,
  Check,
  Plus,
  Minus,
  Heart,
  Star,
  Clock,
  Calendar,
  MapPin,
  Coffee,
  Briefcase,
  GraduationCap,
  Building2,
  ShoppingBag,
  UtensilsCrossed,
  PartyPopper,
  Handshake,
  BookOpen,
  FileText,
  Send,
  Volume2,
  Pause,
  Play,
  RotateCcw,
  TrendingUp,
  BarChart3,
  Target,
  Award,
  Lightbulb,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
  HelpCircle,
  Edit,
  Trash2,
  Copy,
  Share2,
  Download,
  Upload,
  Moon,
  Sun,
  Eye,
  EyeOff,
} from 'lucide-react-native';

export type IconName =
  | 'home'
  | 'user'
  | 'users'
  | 'message'
  | 'mic'
  | 'settings'
  | 'bell'
  | 'search'
  | 'chevronLeft'
  | 'chevronRight'
  | 'arrowRight'
  | 'arrowLeft'
  | 'x'
  | 'check'
  | 'plus'
  | 'minus'
  | 'heart'
  | 'star'
  | 'clock'
  | 'calendar'
  | 'mapPin'
  | 'coffee'
  | 'briefcase'
  | 'graduationCap'
  | 'building'
  | 'shoppingBag'
  | 'utensils'
  | 'party'
  | 'handshake'
  | 'book'
  | 'fileText'
  | 'send'
  | 'volume'
  | 'pause'
  | 'play'
  | 'refresh'
  | 'trendingUp'
  | 'barChart'
  | 'target'
  | 'award'
  | 'lightbulb'
  | 'alertCircle'
  | 'checkCircle'
  | 'xCircle'
  | 'info'
  | 'help'
  | 'edit'
  | 'trash'
  | 'copy'
  | 'share'
  | 'download'
  | 'upload'
  | 'moon'
  | 'sun'
  | 'eye'
  | 'eyeOff';

const ICONS: Record<IconName, React.ComponentType<any>> = {
  home: Home,
  user: User,
  users: Users,
  message: MessageCircle,
  mic: Mic,
  settings: Settings,
  bell: Bell,
  search: Search,
  chevronLeft: ChevronLeft,
  chevronRight: ChevronRight,
  arrowRight: ArrowRight,
  arrowLeft: ArrowLeft,
  x: X,
  check: Check,
  plus: Plus,
  minus: Minus,
  heart: Heart,
  star: Star,
  clock: Clock,
  calendar: Calendar,
  mapPin: MapPin,
  coffee: Coffee,
  briefcase: Briefcase,
  graduationCap: GraduationCap,
  building: Building2,
  shoppingBag: ShoppingBag,
  utensils: UtensilsCrossed,
  party: PartyPopper,
  handshake: Handshake,
  book: BookOpen,
  fileText: FileText,
  send: Send,
  volume: Volume2,
  pause: Pause,
  play: Play,
  refresh: RotateCcw,
  trendingUp: TrendingUp,
  barChart: BarChart3,
  target: Target,
  award: Award,
  lightbulb: Lightbulb,
  alertCircle: AlertCircle,
  checkCircle: CheckCircle,
  xCircle: XCircle,
  info: Info,
  help: HelpCircle,
  edit: Edit,
  trash: Trash2,
  copy: Copy,
  share: Share2,
  download: Download,
  upload: Upload,
  moon: Moon,
  sun: Sun,
  eye: Eye,
  eyeOff: EyeOff,
};

interface IconProps {
  name: IconName;
  size?: number;
  color?: string;
  strokeWidth?: number;
}

export const Icon: React.FC<IconProps> = ({
  name,
  size = 24,
  color = '#1A1A2E',
  strokeWidth = 2,
}) => {
  const IconComponent = ICONS[name];
  
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found`);
    return null;
  }

  return <IconComponent size={size} color={color} strokeWidth={strokeWidth} />;
};

// Export individual icons for direct usage
export {
  Home,
  User,
  Users,
  MessageCircle,
  Mic,
  Settings,
  Bell,
  Search,
  ChevronLeft,
  ChevronRight,
  ArrowRight,
  ArrowLeft,
  X,
  Check,
  Plus,
  Minus,
  Heart,
  Star,
  Clock,
  Calendar,
  MapPin,
  Coffee,
  Briefcase,
  GraduationCap,
  Building2,
  ShoppingBag,
  UtensilsCrossed,
  PartyPopper,
  Handshake,
  BookOpen,
  FileText,
  Send,
  Volume2,
  Pause,
  Play,
  RotateCcw,
  TrendingUp,
  BarChart3,
  Target,
  Award,
  Lightbulb,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
  HelpCircle,
  Edit,
  Trash2,
  Copy,
  Share2,
  Download,
  Upload,
  Moon,
  Sun,
  Eye,
  EyeOff,
};
