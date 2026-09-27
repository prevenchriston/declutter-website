#!/usr/bin/env python3
"""
Declutter Junk Removal — static site builder.

    python3 build.py          # builds everything into ./site

Edit business info, services, areas, FAQs and reviews in the CONTENT section
below. Drop photos into ./photos (see photos/README.md) and rebuild; images are
resized and converted to WebP automatically (needs Pillow: pip3 install Pillow).
"""
import hashlib
import html
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

try:
    from PIL import Image, ImageFilter, ImageOps, ImageDraw
    HAVE_PIL = True
except ImportError:  # still builds; photos are copied as-is
    HAVE_PIL = False

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'site'
PHOTOS = ROOT / 'photos'
STATIC = ROOT / 'static'
BRAND = ROOT / 'brand'
CACHE = ROOT / '.cache'

# ============================================================================
# CONTENT
# ============================================================================
SITE = {
    'name': 'Declutter Junk Removal',
    'short': 'Declutter',
    'url': 'https://www.thedeclutterteam.com',
    'phone': '(316) 749-8109',
    'tel': '+13167498109',
    'email': 'infodeclutterteam@gmail.com',
    'city': 'Wichita',
    'region': 'KS',
    'google': 'https://share.google/5ghHvq0JGjwLNMbYt',
    'instagram': 'https://instagram.com/thedeclutterteam',
    'facebook': 'https://facebook.com/thedeclutterteam',
    'tiktok': 'https://tiktok.com/@thedeclutterteam',
    'tagline': 'Cleaner spaces, brighter days.',
}

SERVICES = [
    {
        'slug': 'garage-cleanouts', 'key': 'garage', 'name': 'Garage Cleanouts', 'icon': 'warehouse',
        'photo': 'service-garage', 'photo_alt': 'A single-car garage in Wichita after a Declutter cleanout, floor cleared and swept',
        'ba': 'two-car-garage',
        'tagline': 'Turn that packed garage back into usable space.',
        'meta': 'Garage cleanouts in Wichita, KS. We haul the junk, organize what stays and sweep up — usually in one visit. Upfront pricing. Free quote: (316) 749-8109.',
        'intro': "Boxes that haven't been opened since the last move, a treadmill nobody uses, broken tools and old furniture — it adds up until the car lives in the driveway. We clear out everything you don't want, help organize what stays, and sweep the floor before we leave.",
        'included': [
            'Hauling away anything non-hazardous you want gone',
            'Sorting with you — you decide what stays and what goes',
            'Organizing what stays so you can find it again',
            'All lifting, loading and hauling done by our crew',
            'A full sweep-out before we leave',
        ],
        'good_for': ['Parking in your garage again', 'Getting a home ready to sell', 'After a move', 'Clearing a workshop', 'A seasonal reset'],
    },
    {
        'slug': 'junk-removal', 'key': 'junk', 'name': 'Junk & Furniture Removal', 'icon': 'sofa',
        'photo': 'service-junk', 'photo_alt': 'Two Declutter crew members carrying an old couch down a wooden ramp',
        'ba': 'two-car-garage',
        'tagline': "Furniture, mattresses, appliances and unwanted household items — we'll haul it away.",
        'meta': 'Junk and furniture removal in Wichita, KS. Couches, mattresses, appliances, electronics and household clutter hauled away. Upfront pricing: (316) 749-8109.',
        'intro': "One old couch or a whole houseful. Point to what you want gone and our crew does the lifting, loading and hauling — you don't have to touch a thing. Items in good shape get donated when possible; the rest is disposed of properly.",
        'included': [
            'Couches, recliners, tables, dressers and bed frames',
            'Mattresses and box springs',
            'Appliances and electronics',
            'Yard waste and general household clutter',
            'Single items or full truckloads',
        ],
        'good_for': ['New furniture on the way', 'Downsizing', 'Spring cleaning', 'Helping a parent move', 'Clearing a spare room'],
    },
    {
        'slug': 'hot-tub-removal', 'key': 'hot-tub', 'name': 'Hot Tub Removal', 'icon': 'waves',
        'photo': 'service-hot-tub', 'photo_alt': 'Declutter crew member cutting down an old hot tub under a backyard pergola',
        'ba': 'hot-tub-removal',
        'tagline': 'We cut it down, haul it off and leave the patio clean.',
        'meta': 'Hot tub removal in Wichita, KS. We dismantle old hot tubs on-site, haul every piece away and clean up the patio. Free quote: (316) 749-8109.',
        'intro': "Old hot tubs are heavy, awkward and usually boxed in by fences, decks and pergolas. Our crew takes them apart right where they sit, carries every piece out, and cleans up behind us — so you get your patio back without renting a trailer or calling in favors.",
        'included': [
            'Cutting down and dismantling the tub on-site',
            'Removing the cabinet, cover and steps',
            'Hauling away every piece',
            'Working carefully around fences, decks and pergolas',
            'Clean-up of the pad or patio when we finish',
        ],
        'good_for': ["A tub that doesn't work anymore", 'Making room for a new one', 'Patio or backyard redos', 'Getting a home ready to sell'],
    },
    {
        'slug': 'property-cleanouts', 'key': 'property', 'name': 'Move-Out & Property Cleanouts', 'icon': 'key',
        'photo': 'cleanout-in-progress', 'photo_alt': 'Declutter crew clearing out a two-car garage during a property cleanout',
        'ba': 'two-car-garage',
        'tagline': 'Fast cleanouts for homeowners, landlords, property managers and real estate professionals.',
        'meta': 'Move-out, rental and whole-property cleanouts in Wichita, KS for homeowners, landlords, property managers and realtors. Residential and commercial. (316) 749-8109.',
        'intro': "Whether it's what a tenant left behind, a house getting ready to list, or a family property that needs to be cleared with care, we handle full cleanouts from the front door to the back fence — so the next step can happen on schedule. Residential and commercial.",
        'included': [
            'Whole-home and full-property cleanouts',
            'Tenant move-out leftovers',
            'Pre-listing cleanouts for real estate agents',
            'Estate and family property cleanouts, handled respectfully',
            'Garages, basements and attics included',
            'A final sweep and walkthrough with you',
        ],
        'good_for': ['Landlords', 'Property managers', 'Real estate agents', 'Families handling an estate', 'Commercial spaces'],
    },
    {
        'slug': 'basement-attic-cleanouts', 'key': 'basement', 'name': 'Basement & Attic Cleanouts', 'icon': 'archive',
        'photo': 'loaded-trailer', 'photo_alt': 'A Declutter trailer loaded with lumber, boxes and bags from a cleanout',
        'ba': 'two-car-garage',
        'tagline': 'Clear years of accumulated clutter without doing the heavy lifting yourself.',
        'meta': 'Basement and attic cleanouts in Wichita, KS. We handle the stairs, tight spaces and heavy lifting, and treat your home with care. Free quote: (316) 749-8109.',
        'intro': "Basements and attics are where things go to be forgotten — and where carrying them out is hardest. We handle the stairs, the tight corners and the heavy lifting, and we're careful with your walls, floors and railings on the way out.",
        'included': [
            'Clearing boxes, old furniture and stored items',
            'Handling stairs, tight corners and awkward access',
            'Careful with walls, floors and railings',
            'Sorting help — keep, donate or haul',
            'Sweep-up when the space is empty',
        ],
        'good_for': ['Finishing a basement', 'Preparing to sell', 'Downsizing', 'After years in the same home'],
    },
]

AREAS = [
    {'slug': 'wichita', 'name': 'Wichita', 'pos': (300, 250), 'anchor': 'start', 'dx': 18, 'dy': 34,
     'intro': "Wichita is home base. From College Hill and Riverside to Delano, Midtown and the newer neighborhoods on the east and west sides, we clear garages, basements, rentals and whole homes across the city — usually with same-week scheduling."},
    {'slug': 'derby', 'name': 'Derby', 'pos': (382, 358), 'anchor': 'start', 'dx': 16, 'dy': 7,
     'intro': "Just south of Wichita, Derby is an easy trip for our crew. Whether it's a garage that has filled up over the years or a move-out on a tight timeline, we'll give you a clear upfront price and do all the heavy lifting."},
    {'slug': 'andover', 'name': 'Andover', 'pos': (458, 240), 'anchor': 'start', 'dx': 16, 'dy': 7,
     'intro': "Out east in Butler County, Andover homeowners call us for garage cleanouts, basement clear-outs, hot tub removal and furniture haul-away. Send a few photos and we'll get you a clear, upfront quote."},
    {'slug': 'maize', 'name': 'Maize', 'pos': (214, 160), 'anchor': 'end', 'dx': -16, 'dy': 7,
     'intro': "On Wichita's northwest side, Maize families call us when the garage, basement or storage room has gotten out of hand. We show up on time, do the lifting, and sweep up after."},
    {'slug': 'park-city', 'name': 'Park City', 'pos': (318, 138), 'anchor': 'start', 'dx': 16, 'dy': 7,
     'intro': "Just north of Wichita along I-135, Park City is right in our regular service area — for single items, full garages and rental property cleanouts."},
    {'slug': 'bel-aire', 'name': 'Bel Aire', 'pos': (388, 182), 'anchor': 'start', 'dx': 16, 'dy': 7,
     'intro': "In Bel Aire, northeast of Wichita, we help homeowners reclaim garages and basements and help landlords turn properties over fast."},
    {'slug': 'haysville', 'name': 'Haysville', 'pos': (282, 352), 'anchor': 'end', 'dx': -16, 'dy': 7,
     'intro': "South of Wichita, Haysville homeowners use Declutter for everything from one old couch to a full-house cleanout — with upfront pricing and no hidden fees."},
    {'slug': 'goddard', 'name': 'Goddard', 'pos': (132, 250), 'anchor': 'middle', 'dx': 0, 'dy': 36,
     'intro': "West of Wichita along US-54, Goddard is part of our regular service area. We handle garage cleanouts, move-outs, hot tubs and furniture and appliance haul-away."},
]

FAQS = [
    ('How much does junk removal cost?',
     'Every job is priced by volume and item type. We give you a clear, upfront quote before any work begins — no hidden fees, no surprises.'),
    ('Do you offer same-day service?',
     'In many cases, yes. Call <a href="tel:+13167498109">(316) 749-8109</a> and we\'ll do our best to fit you in same-day or next-day. Otherwise, we\'ll schedule the earliest time that works for you.'),
    ('What items do you take?',
     'Almost anything non-hazardous: furniture, mattresses, appliances, electronics, hot tubs, yard waste, and general household clutter. Not sure about something? Just ask.'),
    ('Do I need to move anything beforehand?',
     'Nope. Point to what you want gone and our crew does all the lifting, loading, and hauling — you don\'t have to touch a thing.'),
    ('Can you clean out an entire property?',
     'Yes. We handle full cleanouts for homes, garages, basements, attics, and rental properties — ideal for landlords, property managers, and real estate professionals.'),
    ('What happens to my stuff?',
     'Items in good shape are donated when possible. Everything else is hauled to proper disposal facilities — not dumped somewhere it doesn\'t belong.'),
    ('How do I get a quote?',
     'Call or text <a href="tel:+13167498109">(316) 749-8109</a>, or <a href="/contact/">send us a few photos</a> through our quote form. We\'ll get back to you with a clear, upfront price — free, with no obligation.'),
]

# Paste REAL Google reviews here to switch on the reviews carousel, e.g.
# {'quote': '...', 'name': 'First L.', 'where': 'Riverside, Wichita'},
REVIEWS = []

ITEMS_A = ['Furniture', 'Mattresses', 'Appliances', 'Hot tubs', 'Electronics', 'Yard waste']
ITEMS_B = ['Garage clutter', 'Couches', 'Treadmills', 'Boxes', 'Rental leftovers', 'Household junk']

NAV = [
    ('services', 'Services', '/services/'),
    ('areas', 'Service Areas', '/areas/'),
    ('process', 'How It Works', '/#how-it-works'),
    ('about', 'Our Story', '/about/'),
    ('faq', 'FAQ', '/#faq'),
]

# ============================================================================
# ICONS (Lucide-style, 24px grid)
# ============================================================================
ICONS = {
    'phone': '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    'arrow': '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    'arrow-left': '<path d="M19 12H5"/><path d="m12 19-7-7 7-7"/>',
    'check': '<path d="M20 6 9 17l-5-5"/>',
    'shield': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/>',
    'clock': '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    'calendar': '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/><path d="m9 16 2 2 4-4"/>',
    'tag': '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r="1.2"/>',
    'sparkles': '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>',
    'truck': '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/>',
    'warehouse': '<path d="M22 8.35V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8.35A2 2 0 0 1 3.26 6.5l8-3.2a2 2 0 0 1 1.48 0l8 3.2A2 2 0 0 1 22 8.35Z"/><path d="M6 18h12"/><path d="M6 14h12"/><rect width="12" height="12" x="6" y="10"/>',
    'sofa': '<path d="M20 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v3"/><path d="M2 11v5a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5a2 2 0 0 0-4 0v2H6v-2a2 2 0 0 0-4 0Z"/><path d="M4 18v2"/><path d="M20 18v2"/><path d="M12 4v9"/>',
    'waves': '<path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>',
    'key': '<path d="m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"/><path d="m21 2-9.6 9.6"/><circle cx="7.5" cy="15.5" r="5.5"/>',
    'archive': '<rect width="20" height="5" x="2" y="3" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/>',
    'camera': '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>',
    'pin': '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    'message': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    'mail': '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    'star': '<path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"/>',
    'plus': '<path d="M5 12h14"/><path d="M12 5v14"/>',
    'menu': '<path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h10"/>',
    'x': '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    'heart': '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
    'home': '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    'zap': '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',
    'recycle': '<path d="M7 19H4.815a1.83 1.83 0 0 1-1.57-.881 1.785 1.785 0 0 1-.004-1.784L7.196 9.5"/><path d="M11 19h8.203a1.83 1.83 0 0 0 1.556-.89 1.784 1.784 0 0 0 0-1.775l-1.226-2.12"/><path d="m14 16-3 3 3 3"/><path d="M8.293 13.596 7.196 9.5 3.1 10.598"/><path d="m9.344 5.811 1.093-1.892A1.83 1.83 0 0 1 11.985 3a1.784 1.784 0 0 1 1.546.888l3.943 6.843"/><path d="m13.378 9.633 4.096 1.098 1.097-4.096"/>',
    'play': '<path d="M6 4.5v15a1 1 0 0 0 1.5.86l12.5-7.5a1 1 0 0 0 0-1.72L7.5 3.64A1 1 0 0 0 6 4.5z"/>',
    'pause': '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
    'upload': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
    'users': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    'building': '<rect width="16" height="20" x="4" y="2" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/>',
    'dots': '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>',
    'arrows-h': '<path d="m9 7-5 5 5 5"/><path d="m15 7 5 5-5 5"/>',
    'instagram': '<rect width="20" height="20" x="2" y="2" rx="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><path d="M17.5 6.5h.01"/>',
    'facebook': '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
}
FILLED = {'play', 'pause', 'star'}
TIKTOK = '<path class="ic-fill" d="M16.6 5.82A4.28 4.28 0 0 1 15.54 3h-3.09v12.4a2.59 2.59 0 0 1-2.59 2.5c-1.42 0-2.6-1.16-2.6-2.6 0-1.72 1.66-3.01 3.37-2.48V9.66c-3.45-.46-6.47 2.22-6.47 5.64 0 3.33 2.76 5.7 5.69 5.7 3.14 0 5.69-2.55 5.69-5.7V9.01a7.35 7.35 0 0 0 4.3 1.38V7.3s-1.88.09-3.24-1.48z"/>'
LEAF_PATH = 'M4 21c0-9 6.5-17 18-18-.6 10.6-7.4 17.3-16.3 17.9M6 19c3.2-4.6 7-8.2 11.5-10.6'


def icon(name, cls=''):
    body = TIKTOK if name == 'tiktok' else ICONS[name]
    fill = ' ic-fill' if name in FILLED else ''
    extra = f' {cls}' if cls else ''
    return f'<svg class="ic{fill}{extra}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{body}</svg>'


def esc(s):
    return html.escape(s, quote=True)


# ============================================================================
# IMAGES
# ============================================================================
IMG_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.heic')
WIDTHS = (480, 800, 1200, 1800)
IMG_OUT = OUT / 'assets' / 'img'
_img_cache = {}


def find_photo(name):
    base = PHOTOS / name
    for ext in IMG_EXTS:
        for cand in (base.with_suffix(ext), base.with_suffix(ext.upper())):
            if cand.exists():
                return cand
    return None


def process(src):
    if src in _img_cache:
        return _img_cache[src]
    digest = hashlib.md5(src.read_bytes()).hexdigest()[:8]
    stem = re.sub(r'[^a-z0-9]+', '-', src.stem.lower()).strip('-')
    IMG_OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(exist_ok=True)

    if not HAVE_PIL:
        dest = IMG_OUT / f'{stem}-{digest}{src.suffix.lower()}'
        shutil.copy2(src, dest)
        info = {'webp': [], 'jpg': f'/assets/img/{dest.name}', 'w': None, 'h': None}
        _img_cache[src] = info
        return info

    path = src
    if src.suffix.lower() == '.heic':  # iPhone photos: convert with macOS sips
        path = CACHE / f'{stem}-{digest}.jpg'
        if not path.exists():
            subprocess.run(['sips', '-s', 'format', 'jpeg', str(src), '--out', str(path)], check=True, capture_output=True)

    im = None
    W = H = 0
    webp = []
    widths = [w for w in WIDTHS if w <= _peek_width(path)] or [_peek_width(path)]
    for w in widths:
        name = f'{stem}-{digest}-{w}.webp'
        cached = CACHE / name
        if not cached.exists():
            if im is None:
                im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
            h = round(im.height * w / im.width)
            im.resize((w, h), Image.LANCZOS).save(cached, 'WEBP', quality=76, method=6)
        shutil.copy2(cached, IMG_OUT / name)
        webp.append((f'/assets/img/{name}', w))
    fw = min(1200, widths[-1])
    jname = f'{stem}-{digest}-{fw}.jpg'
    cached = CACHE / jname
    if not cached.exists():
        if im is None:
            im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
        h = round(im.height * fw / im.width)
        im.resize((fw, h), Image.LANCZOS).save(cached, 'JPEG', quality=80, optimize=True, progressive=True)
    shutil.copy2(cached, IMG_OUT / jname)
    with Image.open(cached) as j:
        W, H = j.size
    info = {'webp': webp, 'jpg': f'/assets/img/{jname}', 'w': W, 'h': H}
    _img_cache[src] = info
    return info


def _peek_width(path):
    with Image.open(path) as im:
        w, h = im.size
        try:
            if im.getexif().get(274) in (5, 6, 7, 8):  # rotated 90°
                w = h
        except Exception:
            pass
    return w


def img(name, alt, sizes='100vw', eager=False, cls=''):
    src = find_photo(name)
    if not src:
        return placeholder(name)
    d = process(src)
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    dims = f' width="{d["w"]}" height="{d["h"]}"' if d['w'] else ''
    c = f' class="{cls}"' if cls else ''
    tag = f'<img src="{d["jpg"]}" alt="{esc(alt)}"{dims} {load} decoding="async"{c}>'
    if not d['webp']:
        return tag
    srcset = ', '.join(f'{u} {w}w' for u, w in d['webp'])
    return f'<picture><source type="image/webp" srcset="{srcset}" sizes="{sizes}">{tag}</picture>'


def img_url(name, width=800):
    src = find_photo(name)
    if not src:
        return ''
    d = process(src)
    for u, w in d['webp']:
        if w >= width:
            return u
    return d['webp'][-1][0] if d['webp'] else d['jpg']


def placeholder(name, extra=''):
    return (f'<div class="ph {extra}" role="img" aria-label="Photo coming soon">'
            f'<span>{icon("camera")} Add <code>photos/{esc(name)}.jpg</code></span></div>')


def ba_pairs():
    folder = PHOTOS / 'before-after'
    pairs = []
    if folder.exists():
        for f in sorted(folder.iterdir()):
            m = re.match(r'(.+)-before$', f.stem)
            if m and f.suffix.lower() in IMG_EXTS and find_photo(f'before-after/{m.group(1)}-after'):
                pairs.append(m.group(1))
    return pairs


BA_CAPTIONS = {
    'two-car-garage': ('Two-car garage cleanout', 'Wichita, KS · one visit'),
    'hot-tub-removal': ('Hot tub removal', 'Cut down, hauled off, patio rinsed'),
}


def ba(slug, eager=False, ratio='4 / 5'):
    title, sub = BA_CAPTIONS.get(slug, (slug.replace('-', ' ').title(), 'Wichita area'))
    before = img(f'before-after/{slug}-before', f'{title} — before', '(min-width: 760px) 50vw, 100vw', eager)
    after = img(f'before-after/{slug}-after', f'{title} — after', '(min-width: 760px) 50vw, 100vw', eager)
    return f'''<figure class="ba" data-reveal>
  <div class="ba-media" style="--ratio:{ratio}">
    <div class="ba-after">{after}</div>
    <div class="ba-before">{before}</div>
    <span class="tag ba-label ba-label--before">Before</span>
    <span class="tag tag--green ba-label ba-label--after">After</span>
    <input class="ba-range" type="range" min="0" max="100" value="50" aria-label="Compare before and after: {esc(title)}">
    <div class="ba-handle" aria-hidden="true"><span>{icon("arrows-h")}</span></div>
  </div>
  <figcaption><strong>{esc(title)}</strong><span>{esc(sub)}</span></figcaption>
</figure>'''


# ============================================================================
# SHARED PARTIALS
# ============================================================================
def header(active):
    links = []
    for key, label, href in NAV:
        cur = ' aria-current="page"' if key == active else ''
        links.append(f'<a href="{href}"{cur}>{label}</a>')
    mlinks = ''.join(
        f'<a href="{href}" style="--i:{i}">{label}{icon("arrow")}</a>'
        for i, (_, label, href) in enumerate(NAV + [('contact', 'Free Quote', '/contact/')]))
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="/" aria-label="{SITE['short']} Junk Removal — home"><img src="/assets/brand/logo.png" alt="{SITE['short']} Junk Removal" width="{LOGO['w']}" height="{LOGO['h']}"></a>
    <nav class="nav" aria-label="Main">{''.join(links)}</nav>
    <div class="header-cta">
      <a class="header-phone" href="tel:{SITE['tel']}">{icon('phone')}{SITE['phone']}</a>
      <a class="btn btn-primary btn-sm header-quote" href="/contact/">Free Quote</a>
      <button class="menu-btn" type="button" aria-expanded="false" aria-controls="mobile-menu" aria-label="Open menu">{icon('menu', 'ic-menu')}{icon('x', 'ic-close')}</button>
    </div>
  </div>
</header>
<div class="mobile-menu" id="mobile-menu" inert>
  <nav aria-label="Mobile">{mlinks}</nav>
  <div class="mobile-menu-foot">
    <a class="btn btn-primary btn-block" href="tel:{SITE['tel']}">{icon('phone')}Call {SITE['phone']}</a>
    <a class="btn btn-ghost btn-block" href="sms:{SITE['tel']}">{icon('message')}Text us photos</a>
  </div>
</div>'''


def footer():
    svc = ''.join(f'<li><a href="/services/{s["slug"]}/">{s["name"]}</a></li>' for s in SERVICES)
    areas = ''.join(f'<li><a href="/areas/{a["slug"]}/">{a["name"]}</a></li>' for a in AREAS)
    return f'''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <img src="/assets/brand/logo.png" alt="{SITE['short']} Junk Removal" width="{LOGO['w']}" height="{LOGO['h']}" loading="lazy">
        <p>Locally owned junk removal and cleanouts in Wichita, KS. {SITE['tagline']}</p>
        <div class="socials">
          <a href="{SITE['instagram']}" aria-label="Instagram" rel="noopener">{icon('instagram')}</a>
          <a href="{SITE['facebook']}" aria-label="Facebook" rel="noopener">{icon('facebook')}</a>
          <a href="{SITE['tiktok']}" aria-label="TikTok" rel="noopener">{icon('tiktok')}</a>
        </div>
      </div>
      <div class="footer-col"><h2>Services</h2><ul>{svc}</ul></div>
      <div class="footer-col"><h2>Service areas</h2><ul>{areas}</ul></div>
      <div class="footer-col"><h2>Contact</h2><ul>
        <li><a href="tel:{SITE['tel']}">Call {SITE['phone']}</a></li>
        <li><a href="sms:{SITE['tel']}">Text {SITE['phone']}</a></li>
        <li><a href="mailto:{SITE['email']}">{SITE['email']}</a></li>
        <li><a href="/contact/">Get a free quote</a></li>
        <li><a href="/about/">Our story</a></li>
      </ul></div>
    </div>
    <div class="footer-bottom">
      <span>© {date.today().year} {SITE['name']}. All rights reserved.</span>
      <span>Free estimates · Same-week scheduling · Licensed &amp; insured</span>
    </div>
  </div>
</footer>
<div class="action-bar" role="region" aria-label="Quick contact">
  <a class="btn btn-ghost" href="tel:{SITE['tel']}">{icon('phone')}Call</a>
  <a class="btn btn-ghost" href="sms:{SITE['tel']}">{icon('message')}Text</a>
  <a class="btn btn-primary" href="/contact/">Free quote</a>
</div>'''


def cta_band(title_a='Less junk.', title_b='More space.'):
    return f'''<section class="section cta" aria-labelledby="cta-title">
  <div class="container">
    <h2 class="sr-only" id="cta-title">{title_a} {title_b}</h2>
    <div class="fill-text" aria-hidden="true">
      <div class="outline">{title_a}<br>{title_b}</div>
      <div class="fill">{title_a}<br><span class="accent">{title_b}</span></div>
    </div>
    <p class="cta-sub" data-reveal>Get a free, no-obligation estimate. Most cleanouts are finished in a single day.</p>
    <div class="cta-actions" data-reveal>
      <a class="btn btn-primary btn-magnetic" href="/contact/">Get my free quote{icon('arrow', 'ic-arrow')}</a>
      <a class="btn btn-ghost" href="tel:{SITE['tel']}">{icon('phone')}Call {SITE['phone']}</a>
    </div>
    <p class="cta-note" data-reveal><span>{icon('check')}Free estimates</span><span>{icon('check')}Same-week scheduling</span><span>{icon('check')}Licensed &amp; insured</span></p>
  </div>
</section>'''


def faq_list(items, dark=False):
    out = []
    for q, a in items:
        out.append(f'''<details class="faq-item">
  <summary>{esc(q)}<span class="faq-icon">{icon('plus')}</span></summary>
  <div class="faq-a"><p>{a}</p></div>
</details>''')
    cls = ' dark-faq' if dark else ''
    return f'<div class="faq-list{cls}" data-reveal>{"".join(out)}</div>'


def svc_cards(level='h3'):
    cards = []
    for i, s in enumerate(SERVICES):
        sizes = '(min-width: 1080px) 50vw, (min-width: 700px) 50vw, 100vw' if i < 2 else '(min-width: 1080px) 33vw, (min-width: 700px) 50vw, 100vw'
        cards.append(f'''<article class="svc-card" data-reveal>
  <div class="svc-media">{img(s['photo'], s['photo_alt'], sizes)}</div>
  <div class="svc-body">
    <span class="svc-num">0{i + 1}</span>
    <{level} class="h3">{s['name']}</{level}>
    <p>{esc(s['tagline'])}</p>
    <span class="link-arrow">Learn more{icon('arrow')}</span>
  </div>
  <a class="cover" href="/services/{s['slug']}/" aria-label="{esc(s['name'])}"></a>
</article>''')
    return f'<div class="svc-grid">{"".join(cards)}</div>'


def marquee():
    def group(items, hidden):
        inner = ''.join(f'<span class="marquee-item">{t}{icon("sparkles")}</span>' for t in items)
        attr = ' aria-hidden="true"' if hidden else ''
        return f'<div class="marquee-group"{attr}>{inner}</div>'
    a = group(ITEMS_A, False) + group(ITEMS_A, True)
    b = group(ITEMS_B, False) + group(ITEMS_B, True)
    listed = ', '.join(ITEMS_A + ITEMS_B).lower()
    return f'''<div class="marquee-wrap" aria-label="What we haul">
  <p class="sr-only">We take almost anything non-hazardous, including {listed}.</p>
  <div class="marquee" aria-hidden="true"><div class="marquee-track">{a}</div></div>
  <div class="marquee marquee--rev" aria-hidden="true"><div class="marquee-track">{b}</div></div>
</div>'''


def area_map(current=None):
    rings = ('<circle class="ring-fill" cx="300" cy="250" r="220"/>'
             '<circle class="ring" cx="300" cy="250" r="120"/><circle class="ring" cx="300" cy="250" r="220"/>')
    roads = ('<path class="road road--major" d="M322 20 L318 140 L305 250 L300 470"/>'  # I-135 / I-35
             '<path class="road road--major" d="M20 252 L300 250 L580 236"/>'          # US-54/400 (Kellogg)
             '<path class="road" d="M214 160 C 250 110, 360 110, 420 170 S 470 290, 400 350"/>'  # K-96
             '<path class="road" d="M300 250 L382 358 L420 460"/>'                      # K-15
             '<path class="road" d="M150 60 L214 160"/>')
    river = '<path class="river" d="M120 40 C 190 110, 250 170, 285 230 S 330 330, 318 470"/>'
    cities = []
    for a in AREAS:
        x, y = a['pos']
        hub = a['slug'] == 'wichita'
        cur = a['slug'] == current
        cls = 'map-city' + (' is-hub' if hub else '')
        cur_attr = ' aria-current="page"' if cur else ''
        core_style = ' style="fill:#fff"' if cur and not hub else ''
        r = 11 if hub else 7
        cities.append(
            f'<a class="{cls}" href="/areas/{a["slug"]}/" aria-label="Junk removal in {a["name"]}"'
            f'{cur_attr}>'
            f'<circle class="halo" cx="{x}" cy="{y}" r="{r + 8}"/>'
            f'<circle class="core" cx="{x}" cy="{y}" r="{r}"{core_style}/>'
            f'<text x="{x + a["dx"]}" y="{y + a["dy"]}" text-anchor="{a["anchor"]}">{a["name"]}</text></a>')
    return f'''<div class="map-card" data-reveal>
  <svg class="map" viewBox="0 0 600 480" role="img" aria-label="Map of the Wichita area towns Declutter serves">
    {rings}{roads}{river}{''.join(cities)}
  </svg>
  <span class="map-note">Wichita metro · not to scale</span>
</div>'''


# ============================================================================
# SCHEMA
# ============================================================================
def business_schema():
    return {
        '@context': 'https://schema.org',
        '@type': 'HomeAndConstructionBusiness',
        '@id': SITE['url'] + '/#business',
        'name': SITE['name'],
        'alternateName': 'The Declutter Team',
        'url': SITE['url'] + '/',
        'telephone': SITE['tel'],
        'email': SITE['email'],
        'logo': SITE['url'] + '/assets/brand/logo.png',
        'image': SITE['url'] + '/assets/brand/og.jpg',
        'description': 'Junk removal, garage cleanouts, hot tub removal and property cleanouts in Wichita, KS.',
        'address': {'@type': 'PostalAddress', 'addressLocality': 'Wichita', 'addressRegion': 'KS', 'addressCountry': 'US'},
        'areaServed': [{'@type': 'City', 'name': f'{a["name"]}, KS'} for a in AREAS],
        'sameAs': [SITE['instagram'], SITE['facebook'], SITE['tiktok']],
        'hasOfferCatalog': {
            '@type': 'OfferCatalog', 'name': 'Junk removal services',
            'itemListElement': [{'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': s['name'], 'url': f'{SITE["url"]}/services/{s["slug"]}/'}} for s in SERVICES],
        },
    }


def faq_schema(items):
    strip = lambda s: re.sub(r'<[^>]+>', '', s)
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': strip(a)}} for q, a in items]}


def crumbs_schema(trail):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE['url'] + u} for i, (n, u) in enumerate(trail)]}


def crumbs(trail):
    items = ''.join(
        f'<li><a href="{u}">{n}</a></li>' if i < len(trail) - 1 else f'<li aria-current="page">{n}</li>'
        for i, (n, u) in enumerate(trail))
    return f'<nav aria-label="Breadcrumb"><ol class="crumbs">{items}</ol></nav>'


# ============================================================================
# PAGE SHELL
# ============================================================================
PAGES = []  # for sitemap
ASSET_V = {}


def page(path, title, desc, main, active='', schema=(), noindex=False, preload=''):
    url = SITE['url'] + '/' + path
    canonical = url if not path.endswith('.html') else SITE['url'] + '/'
    ld = ''.join(f'<script type="application/ld+json">{json.dumps(s, separators=(",", ":"))}</script>' for s in schema)
    robots = '<meta name="robots" content="noindex">' if noindex else ''
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
{robots}
<meta name="theme-color" content="#0B0E0C">
<meta name="color-scheme" content="dark">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE['name']}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE['url']}/assets/brand/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/brand/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,500..900&family=Instrument+Sans:wght@400..700&display=swap">
<link rel="stylesheet" href="/assets/css/styles.css?v={ASSET_V['css']}">
{preload}
<script>document.documentElement.classList.add('js');setTimeout(function(){{if(!window.gsap)document.documentElement.classList.add('no-anim')}},3000)</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js" defer></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js" defer></script>
<script src="/assets/js/main.js?v={ASSET_V['js']}" defer></script>
{ld}
</head>
<body>
{header(active)}
<main id="main">
{main}
</main>
{footer()}
</body>
</html>
'''
    dest = OUT / path if path.endswith('.html') else OUT / path / 'index.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(re.sub(r'\n{2,}', '\n', doc), encoding='utf-8')
    if not noindex:
        PAGES.append(canonical)


# ============================================================================
# PAGES
# ============================================================================
def home():
    poster = img_url('before-after/two-car-garage-before', 800)
    hero = f'''<section class="hero" aria-labelledby="hero-title">
  <svg class="leaf-deco" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width=".6" aria-hidden="true"><path d="{LEAF_PATH}"/></svg>
  <div class="container hero-grid">
    <div class="hero-copy">
      <span class="eyebrow" data-hero>Junk removal &amp; cleanouts · Wichita, KS</span>
      <h1 id="hero-title"><span class="line"><span>Less junk.</span></span><span class="line"><span class="accent">More space.</span></span></h1>
      <p class="lead" data-hero>Declutter clears out the junk, organizes what stays, and leaves your space swept clean — usually in a single visit. Clear, upfront pricing and no hidden fees.</p>
      <div class="hero-actions" data-hero>
        <a class="btn btn-primary btn-magnetic" href="/contact/">Get a free quote{icon('arrow', 'ic-arrow')}</a>
        <a class="btn btn-ghost" href="tel:{SITE['tel']}">{icon('phone')}{SITE['phone']}</a>
      </div>
      <ul class="hero-ticks" data-hero>
        <li>{icon('shield')}Licensed &amp; insured</li>
        <li>{icon('calendar')}Same-week service</li>
        <li>{icon('tag')}Upfront pricing</li>
      </ul>
    </div>
    <div class="hero-visual">
      <div class="video-card">
        <video data-hero-video data-src="/assets/video/garage-timelapse.mp4" poster="{poster}" muted loop playsinline preload="none" aria-label="Time-lapse of the Declutter crew clearing a packed two-car garage in Wichita"></video>
        <span class="tag video-tag"><span class="dot"></span>Real job · Wichita</span>
        <button class="video-toggle" type="button" aria-pressed="false" aria-label="Pause video">{icon('pause', 'ic-pause')}{icon('play', 'ic-play')}</button>
        <div class="video-hud" aria-hidden="true">
          <div class="video-hud-row"><span>Before</span><span class="after">After</span></div>
          <div class="video-progress"><span></span></div>
        </div>
      </div>
      <div class="chip-float chip-float--a"><span class="chip-ic">{icon('clock')}</span><div><strong>Cleared in one visit</strong><span>Two-car garage, start to sweep</span></div></div>
      <div class="chip-float chip-float--b"><span class="chip-ic">{icon('star')}</span><div><strong>5-star rated</strong><span>on Google</span></div></div>
    </div>
  </div>
</section>'''

    trust = f'''<section class="trust" aria-label="Why homeowners choose Declutter">
  <div class="container trust-grid">
    <div class="trust-item" data-reveal>{icon('shield')}<div><strong>Licensed &amp; insured</strong><span>Your home is protected</span></div></div>
    <div class="trust-item" data-reveal>{icon('tag')}<div><strong>Upfront pricing</strong><span>A clear quote before we start</span></div></div>
    <div class="trust-item" data-reveal>{icon('calendar')}<div><strong>Same-week service</strong><span>Same-day when we can</span></div></div>
    <div class="trust-item" data-reveal>{icon('recycle')}<div><strong>Donation &amp; disposal</strong><span>Handled the right way</span></div></div>
  </div>
</section>'''

    services = f'''<section class="section" id="services" aria-labelledby="svc-title">
  <div class="container">
    <div class="section-head section-head--split">
      <div style="display:grid;gap:18px">
        <span class="eyebrow" data-reveal>Our services</span>
        <h2 class="h2" id="svc-title" data-split>What can we help you clear out?</h2>
      </div>
      <p class="lead" data-reveal>From a single couch to a whole property, one crew handles the lifting, loading, hauling and clean-up.</p>
    </div>
    {svc_cards()}
  </div>
</section>'''

    pairs = ba_pairs()
    strip_photos = [
        ('service-hot-tub', 'Crew member cutting down a hot tub with a reciprocating saw'),
        ('crew-vests', 'Two Declutter crew members in branded safety vests at the transfer station'),
        ('service-junk', 'Crew carrying a worn-out couch down a ramp'),
        ('disposal-dumpster', 'A full load being unloaded for proper disposal'),
        ('garage-after-wide', 'A two-car garage nearly empty after a cleanout'),
        ('crew-member', 'A Declutter crew member on a garage cleanout job'),
    ]
    strip = ''.join(
        f'<figure class="strip-item">{img(n, a, "(min-width: 760px) 30vw, 70vw")}</figure>'
        for n, a in strip_photos if find_photo(n))
    results = f'''<section class="section surface" id="results" aria-labelledby="results-title">
  <div class="container">
    <div class="section-head section-head--split">
      <div style="display:grid;gap:18px">
        <span class="eyebrow" data-reveal>Real results</span>
        <h2 class="h2" id="results-title" data-split>Drag to see the difference.</h2>
      </div>
      <p class="lead" data-reveal>These are our jobs, not stock photos. Same angle, same day — before we showed up and after we left.</p>
    </div>
    <div class="ba-grid">{''.join(ba(p) for p in pairs)}</div>
  </div>
  <div data-scroller style="margin-top:clamp(56px,8vw,96px)">
    <div class="container section-head section-head--split" style="margin-bottom:28px">
      <h3 class="h3" data-reveal>On the job around Wichita</h3>
      <div class="strip-controls" data-reveal>
        <button class="icon-btn" type="button" data-dir="-1" aria-label="Scroll photos left">{icon('arrow-left')}</button>
        <button class="icon-btn" type="button" data-dir="1" aria-label="Scroll photos right">{icon('arrow')}</button>
      </div>
    </div>
    <div class="strip" data-track tabindex="0" aria-label="Photos from recent jobs">{strip}</div>
  </div>
</section>'''

    process_steps = [
        ('Show us what needs to go', 'Send a few photos by text or through our quote form — or schedule a free estimate.'),
        ('Get your upfront price', "We'll give you a clear quote before any work begins. No hidden fees, no surprises."),
        ('We do the heavy lifting', 'Our crew removes, loads and hauls everything away. You just point.'),
        ('Enjoy your space again', 'We clean up behind ourselves and leave you with a clutter-free space.'),
    ]
    steps = ''.join(f'''<li class="step" data-reveal><span class="step-num">{i + 1}</span><h3 class="h3">{t}</h3><p>{d}</p></li>'''
                    for i, (t, d) in enumerate(process_steps))
    process = f'''<section class="section paper" id="how-it-works" aria-labelledby="process-title">
  <div class="container process-grid">
    <div class="section-head">
      <span class="eyebrow" data-reveal>Simple process</span>
      <h2 class="h2" id="process-title" data-split>Getting started is easy.</h2>
      <p class="lead" data-reveal>Four steps, usually one visit. Most customers go from first text to empty garage within the same week.</p>
      <div data-reveal style="margin-top:12px"><a class="btn btn-dark" href="/contact/">Start with a few photos{icon('arrow', 'ic-arrow')}</a></div>
    </div>
    <ol class="steps"><span class="steps-line" aria-hidden="true"><i></i></span>{steps}</ol>
  </div>
</section>'''

    crew = f'''<section class="section" aria-labelledby="crew-title">
  <div class="container split">
    <div class="media-stack" data-reveal>
      <div class="media-main" data-parallax>{img('crew-member', 'A Declutter crew member standing in front of a garage he just cleared', '(min-width: 960px) 45vw, 100vw')}</div>
      <div class="media-sub">{img('crew-vests', 'Declutter crew in branded safety vests', '(min-width: 960px) 20vw, 44vw')}</div>
    </div>
    <div>
      <span class="eyebrow" data-reveal>Local crew</span>
      <h2 class="h2" id="crew-title" data-split style="margin-top:18px">More than junk removal. We're here to help.</h2>
      <p class="lead" data-reveal style="margin-top:22px">Clearing out a garage, a home or a rental can feel overwhelming. Our goal is to make it easy — from the first message to the final walkthrough.</p>
      <ul class="feature-list">
        <li data-reveal><span class="fi">{icon('clock')}</span><div><strong>We show up on time</strong><p>And we communicate clearly the whole way through.</p></div></li>
        <li data-reveal><span class="fi">{icon('home')}</span><div><strong>We respect your home</strong><p>Your property is treated the way we'd want ours treated.</p></div></li>
        <li data-reveal><span class="fi">{icon('pin')}</span><div><strong>We're local</strong><p>Building our reputation in Wichita one cleanout at a time.</p></div></li>
      </ul>
      <div data-reveal style="margin-top:36px"><a class="link-arrow" href="/about/">Read our story{icon('arrow')}</a></div>
    </div>
  </div>
</section>'''

    disposal = f'''<section class="section surface" aria-labelledby="disposal-title">
  <div class="container split split--rev">
    <div class="media-stack" data-reveal>
      <div class="media-main" data-parallax>{img('disposal-dumpster', 'A Declutter crew member unloading a full load at a local transfer station', '(min-width: 960px) 45vw, 100vw')}</div>
    </div>
    <div>
      <span class="eyebrow" data-reveal>Donation &amp; disposal</span>
      <h2 class="h2" id="disposal-title" data-split style="margin-top:18px">Out of your home. Off your mind.</h2>
      <p class="lead" data-reveal style="margin-top:22px">We don't just move your junk out of sight. Items in good shape are donated when possible, and everything else goes to proper disposal facilities — never dumped where it doesn't belong.</p>
      <ul class="checks" style="margin-top:30px">
        <li data-reveal><span class="ci">{icon('check')}</span>Usable items donated when possible</li>
        <li data-reveal><span class="ci">{icon('check')}</span>Hauled to proper Wichita-area facilities</li>
        <li data-reveal><span class="ci">{icon('check')}</span>Disposal included in your upfront price</li>
      </ul>
    </div>
  </div>
</section>'''

    if REVIEWS:
        cards = ''.join(f'''<article class="review"><div class="stars" aria-label="5 out of 5 stars">{icon('star') * 5}</div>
<blockquote>“{esc(r['quote'])}”</blockquote><footer><strong>{esc(r['name'])}</strong>{esc(r.get('where', ''))}</footer></article>''' for r in REVIEWS)
        review_block = f'''<div data-scroller style="margin-top:32px">
  <div class="review-track" data-track tabindex="0" aria-label="Customer reviews">{cards}</div>
  <div class="strip-controls" style="margin-top:20px"><button class="icon-btn" type="button" data-dir="-1" aria-label="Previous review">{icon('arrow-left')}</button><button class="icon-btn" type="button" data-dir="1" aria-label="Next review">{icon('arrow')}</button></div>
</div>'''
    else:
        review_block = ''
    reviews = f'''<section class="section" aria-labelledby="reviews-title">
  <div class="container">
    <div class="rating-panel" data-reveal>
      <div><div class="rating-score">5.0</div><div class="stars" aria-label="Rated 5 out of 5 stars">{icon('star') * 5}</div></div>
      <div class="rating-copy">
        <span class="eyebrow">Reviews</span>
        <h2 class="h3" id="reviews-title" style="font-size:clamp(1.5rem,2.6vw,2.1rem)">Rated 5 stars on Google by Wichita homeowners.</h2>
        <p>We earn every review by treating each customer like they're our only one. See what our neighbors are saying.</p>
      </div>
      <a class="btn btn-ghost" href="{SITE['google']}" rel="noopener">Read our Google reviews{icon('arrow', 'ic-arrow')}</a>
    </div>
    {review_block}
  </div>
</section>'''

    area_links = ''.join(f'<a href="/areas/{a["slug"]}/">{a["name"]}{icon("arrow")}</a>' for a in AREAS)
    areas = f'''<section class="section surface" id="areas" aria-labelledby="areas-title">
  <div class="container areas-grid">
    <div>
      <span class="eyebrow" data-reveal>Service area</span>
      <h2 class="h2" id="areas-title" data-split style="margin-top:18px">Proudly serving Wichita &amp; nearby towns.</h2>
      <p class="lead" data-reveal style="margin-top:22px">Based in Wichita and serving the surrounding communities. Don't see your town? Call us — there's a good chance we can still help.</p>
      <nav class="area-links" aria-label="Service areas" data-reveal>{area_links}</nav>
    </div>
    {area_map()}
  </div>
</section>'''

    faq = f'''<section class="section paper" id="faq" aria-labelledby="faq-title">
  <div class="container faq-grid">
    <div class="section-head">
      <span class="eyebrow" data-reveal>FAQ</span>
      <h2 class="h2" id="faq-title" data-split>Questions, answered.</h2>
      <div class="contact-card" data-reveal>
        <p style="color:var(--ink-muted)">Still wondering about something?</p>
        <a href="tel:{SITE['tel']}">{icon('phone')}{SITE['phone']}</a>
        <a href="mailto:{SITE['email']}">{icon('mail')}{SITE['email']}</a>
      </div>
    </div>
    {faq_list(FAQS)}
  </div>
</section>'''

    main = hero + trust + services + marquee() + results + process + crew + disposal + reviews + areas + faq + cta_band()
    page('', 'Junk Removal & Garage Cleanouts in Wichita, KS | Declutter',
         'Wichita junk removal crew for garages, hot tubs, furniture, basements and whole-property cleanouts. Upfront pricing, same-week service, licensed & insured. Free quote: (316) 749-8109.',
         main, schema=[business_schema(), faq_schema(FAQS)],
         preload=f'<link rel="preload" as="image" href="{poster}">' if poster else '')


def services_index():
    trail = [('Home', '/'), ('Services', '/services/')]
    main = f'''<section class="page-hero">
  <div class="container page-hero-copy">
    {crumbs(trail)}
    <span class="eyebrow">Services</span>
    <h1 class="h1" data-split>Whatever needs to go, we'll haul it.</h1>
    <p class="lead" data-reveal>Garages, hot tubs, furniture, basements and whole properties across Wichita and nearby towns — with clear upfront pricing and a crew that cleans up after itself.</p>
  </div>
</section>
<section class="section" style="padding-top:0"><div class="container">{svc_cards('h2')}</div></section>
{marquee()}
{cta_band()}'''
    page('services/', 'Junk Removal Services in Wichita, KS | Declutter',
         'Garage cleanouts, junk and furniture removal, hot tub removal, move-out and property cleanouts, and basement & attic cleanouts in Wichita, KS.',
         main, active='services', schema=[crumbs_schema(trail)])


def service_page(s):
    trail = [('Home', '/'), ('Services', '/services/'), (s['name'], f'/services/{s["slug"]}/')]
    included = ''.join(f'<li data-reveal><span class="ci">{icon("check")}</span>{esc(t)}</li>' for t in s['included'])
    chips = ''.join(f'<span class="chip">{esc(t)}</span>' for t in s['good_for'])
    others = ''.join(f'<a class="link-tile" href="/services/{o["slug"]}/">{o["name"]}{icon("arrow")}</a>' for o in SERVICES if o is not s)
    area_tiles = ''.join(f'<a class="link-tile" href="/areas/{a["slug"]}/">{s["name"].split(" &")[0]} in {a["name"]}{icon("arrow")}</a>' for a in AREAS[:6])
    faqs = [FAQS[0], FAQS[3], FAQS[1], FAQS[5]]
    main = f'''<section class="page-hero">
  <div class="container page-hero-grid">
    <div class="page-hero-copy">
      {crumbs(trail)}
      <span class="eyebrow">{icon(s['icon'])} {s['name']} · Wichita, KS</span>
      <h1 class="h1" data-split>{s['name']}</h1>
      <p class="lead" data-reveal>{esc(s['tagline'])}</p>
      <div class="hero-actions" data-reveal>
        <a class="btn btn-primary btn-magnetic" href="/contact/?service={s['key']}">Get a free quote{icon('arrow', 'ic-arrow')}</a>
        <a class="btn btn-ghost" href="tel:{SITE['tel']}">{icon('phone')}{SITE['phone']}</a>
      </div>
    </div>
    <div class="page-hero-media" data-reveal data-parallax>{img(s['photo'], s['photo_alt'], '(min-width: 980px) 42vw, 100vw', eager=True)}</div>
  </div>
</section>
<section class="section surface">
  <div class="container two-col">
    <div>
      <span class="eyebrow" data-reveal>How we help</span>
      <h2 class="h2" data-split style="margin-top:18px">What's included</h2>
      <p class="lead" data-reveal style="margin:22px 0 30px">{esc(s['intro'])}</p>
      <ul class="checks">{included}</ul>
    </div>
    <div style="display:grid;gap:20px;align-content:start">
      <div class="card" data-reveal><h3 class="h3">Great for</h3><div class="chips">{chips}</div></div>
      {ba(s['ba'], ratio='4 / 4.2')}
    </div>
  </div>
</section>
<section class="section section--tight">
  <div class="container">
    <div class="section-head"><span class="eyebrow" data-reveal>How it works</span><h2 class="h2" data-split>Four steps. Usually one visit.</h2></div>
    <ol class="mini-steps">
      <li data-reveal><strong>Send photos</strong><p>Text us or use the quote form.</p></li>
      <li data-reveal><strong>Get your price</strong><p>Clear and upfront, before work begins.</p></li>
      <li data-reveal><strong>We haul it</strong><p>All lifting, loading and hauling.</p></li>
      <li data-reveal><strong>Enjoy the space</strong><p>We sweep up before we leave.</p></li>
    </ol>
  </div>
</section>
<section class="section surface">
  <div class="container faq-grid">
    <div class="section-head"><span class="eyebrow" data-reveal>FAQ</span><h2 class="h2" data-split>Good to know</h2></div>
    {faq_list(faqs, dark=True)}
  </div>
</section>
<section class="section section--tight">
  <div class="container">
    <h2 class="h3" data-reveal style="margin-bottom:22px">Other services</h2>
    <div class="link-grid" data-reveal>{others}</div>
    <h2 class="h3" data-reveal style="margin:48px 0 22px">Serving nearby</h2>
    <div class="link-grid" data-reveal>{area_tiles}</div>
  </div>
</section>
{cta_band()}'''
    svc_schema = {'@context': 'https://schema.org', '@type': 'Service', 'name': s['name'], 'serviceType': s['name'],
                  'description': s['intro'], 'provider': {'@id': SITE['url'] + '/#business'},
                  'areaServed': [f'{a["name"]}, KS' for a in AREAS], 'url': f'{SITE["url"]}/services/{s["slug"]}/'}
    page(f'services/{s["slug"]}/', f'{s["name"]} in Wichita, KS | Declutter', s['meta'], main,
         active='services', schema=[business_schema(), svc_schema, faq_schema(faqs), crumbs_schema(trail)])


def areas_index():
    trail = [('Home', '/'), ('Service Areas', '/areas/')]
    area_links = ''.join(f'<a href="/areas/{a["slug"]}/">{a["name"]}{icon("arrow")}</a>' for a in AREAS)
    main = f'''<section class="page-hero">
  <div class="container areas-grid">
    <div class="page-hero-copy">
      {crumbs(trail)}
      <span class="eyebrow">Service areas</span>
      <h1 class="h1" data-split>Wichita &amp; nearby towns.</h1>
      <p class="lead" data-reveal>Based in Wichita and serving the surrounding communities. Pick your town, or just call — if you're near Wichita, there's a good chance we can help.</p>
      <nav class="area-links" aria-label="Service areas" data-reveal style="width:100%">{area_links}</nav>
    </div>
    {area_map()}
  </div>
</section>
{cta_band()}'''
    page('areas/', 'Service Areas — Junk Removal Near Wichita, KS | Declutter',
         'Declutter serves Wichita, Derby, Andover, Maize, Park City, Bel Aire, Haysville and Goddard, KS with junk removal and cleanouts.',
         main, active='areas', schema=[business_schema(), crumbs_schema(trail)])


def area_page(a):
    trail = [('Home', '/'), ('Service Areas', '/areas/'), (a['name'], f'/areas/{a["slug"]}/')]
    svc_tiles = ''.join(f'<a class="link-tile" href="/services/{s["slug"]}/">{s["name"]}{icon("arrow")}</a>' for s in SERVICES)
    nearby = ''.join(f'<a class="link-tile" href="/areas/{o["slug"]}/">{o["name"]}{icon("arrow")}</a>' for o in AREAS if o is not a)
    faqs = [FAQS[0], FAQS[1], FAQS[2], FAQS[6]]
    main = f'''<section class="page-hero">
  <div class="container areas-grid">
    <div class="page-hero-copy">
      {crumbs(trail)}
      <span class="eyebrow">{icon('pin')} {a['name']}, Kansas</span>
      <h1 class="h1" data-split>Junk removal in {a['name']}, KS</h1>
      <p class="lead" data-reveal>{esc(a['intro'])}</p>
      <div class="hero-actions" data-reveal>
        <a class="btn btn-primary btn-magnetic" href="/contact/">Get a free quote{icon('arrow', 'ic-arrow')}</a>
        <a class="btn btn-ghost" href="tel:{SITE['tel']}">{icon('phone')}{SITE['phone']}</a>
      </div>
      <ul class="hero-ticks" data-reveal>
        <li>{icon('shield')}Licensed &amp; insured</li><li>{icon('calendar')}Same-week service</li><li>{icon('tag')}Upfront pricing</li>
      </ul>
    </div>
    {area_map(current=a['slug'])}
  </div>
</section>
<section class="section surface">
  <div class="container">
    <div class="section-head"><span class="eyebrow" data-reveal>Services in {a['name']}</span><h2 class="h2" data-split>What we clear out in {a['name']}</h2></div>
    <div class="link-grid" data-reveal>{svc_tiles}</div>
    <div class="ba-grid" style="margin-top:clamp(48px,6vw,80px)">{''.join(ba(p) for p in ba_pairs())}</div>
  </div>
</section>
<section class="section">
  <div class="container faq-grid">
    <div class="section-head"><span class="eyebrow" data-reveal>FAQ</span><h2 class="h2" data-split>Questions from {a['name']} homeowners</h2></div>
    {faq_list(faqs, dark=True)}
  </div>
</section>
<section class="section section--tight surface">
  <div class="container"><h2 class="h3" data-reveal style="margin-bottom:22px">Also serving</h2><div class="link-grid" data-reveal>{nearby}</div></div>
</section>
{cta_band()}'''
    page(f'areas/{a["slug"]}/', f'Junk Removal in {a["name"]}, KS | Declutter',
         f'Junk removal, garage cleanouts, hot tub removal and property cleanouts in {a["name"]}, KS. Upfront pricing, same-week service. Call (316) 749-8109.',
         main, active='areas', schema=[business_schema(), faq_schema(faqs), crumbs_schema(trail)])


def about():
    trail = [('Home', '/'), ('Our Story', '/about/')]
    reasons = [
        ('heart', 'We serve with passion', 'We genuinely care about the work we do and the people we do it for. Every job matters, whether it\'s one item or an entire property.'),
        ('home', 'We treat your home with respect', 'Your property is treated like we\'d want our own homes treated — carefully and respectfully.'),
        ('sparkles', 'We keep it simple', 'Clear communication, straightforward estimates, and no unnecessary headaches.'),
        ('zap', 'We work hard', 'When we show up, we\'re there to get the job done right and leave you with a space you can finally enjoy again.'),
        ('pin', 'We\'re local', 'We\'re building our reputation right here in the Wichita community, one customer and one cleanout at a time.'),
        ('star', 'We earn every review', 'We\'re proud to be rated 5 stars on Google — because we treat every customer like they\'re our only one.'),
    ]
    rs = ''.join(f'<li data-reveal><span class="fi">{icon(i)}</span><div><strong>{t}</strong><p>{d}</p></div></li>' for i, t, d in reasons)
    crew_poster = img_url('crew-member', 800)
    video = ''
    if (PHOTOS / 'video' / 'crew-intro.mp4').exists():
        video = f'''<div class="video-block" data-reveal><video src="/assets/video/crew-intro.mp4" poster="{crew_poster}" controls playsinline preload="none" aria-label="Meet a member of the Declutter crew"></video></div>'''
    main = f'''<section class="page-hero">
  <div class="container page-hero-grid">
    <div class="page-hero-copy">
      {crumbs(trail)}
      <span class="eyebrow">Our story</span>
      <h1 class="h1" data-split>More than junk removal. We're here to help.</h1>
      <p class="lead" data-reveal>The Declutter Team started with a simple idea: work hard, treat people right, and leave every space better than we found it.</p>
    </div>
    <div class="page-hero-media" data-reveal data-parallax>{img('crew-team', 'The Declutter crew giving a thumbs up in front of a fully loaded box truck after a Wichita cleanout', '(min-width: 980px) 42vw, 100vw', eager=True)}</div>
  </div>
</section>
<section class="section surface">
  <div class="container split">
    <div class="prose">
      <span class="eyebrow" data-reveal>Who we are</span>
      <h2 class="h2" data-split style="margin:18px 0 28px">A local team that shows up.</h2>
      <p data-reveal>We know that clearing out a garage, home, rental property, or unwanted belongings can feel overwhelming. Sometimes it's just clutter that's piled up over the years. Other times, it comes during a move, a life change, or a fresh start. Whatever the reason, our goal is to make the process as easy and stress-free as possible.</p>
      <p data-reveal>We're a local team that believes in showing up on time, communicating clearly, respecting your property, and putting real effort into every job we take on. We're not here just to haul things away — we want every customer to feel taken care of from the first message to the final walkthrough.</p>
    </div>
    {video or f'<div class="media-main" data-reveal>{img("crew-member", "A Declutter crew member", "(min-width: 960px) 45vw, 100vw")}</div>'}
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow" data-reveal>Why Declutter</span><h2 class="h2" data-split>Why trust the Declutter Team?</h2></div>
    <ul class="feature-list" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:36px 48px;margin-top:0">{rs}</ul>
  </div>
</section>
<section class="section surface">
  <div class="container split split--rev">
    <div class="media-stack" data-reveal>
      <div class="media-main" data-parallax>{img('disposal-dumpster', 'Unloading a full load at a local transfer station', '(min-width: 960px) 45vw, 100vw')}</div>
      <div class="media-sub">{img('service-hot-tub', 'Cutting down an old hot tub', '(min-width: 960px) 20vw, 44vw')}</div>
    </div>
    <div>
      <span class="eyebrow" data-reveal>Donation &amp; disposal</span>
      <h2 class="h2" data-split style="margin-top:18px">We finish the job — all the way.</h2>
      <p class="lead" data-reveal style="margin-top:22px">Usable items get donated when possible. Everything else goes to proper disposal facilities. And before we leave your place, we sweep up.</p>
    </div>
  </div>
</section>
{cta_band()}'''
    page('about/', 'Our Story | Declutter Junk Removal — Wichita, KS',
         'Meet the Declutter Team — a local Wichita junk removal crew that shows up on time, respects your home, and leaves every space better than we found it.',
         main, active='about', schema=[business_schema(), crumbs_schema(trail)])


def contact():
    trail = [('Home', '/'), ('Free Quote', '/contact/')]
    svc_opts = ''.join(
        f'<label class="opt"><input type="radio" name="service" value="{esc(s["name"])}" data-key="{s["key"]}"{" required" if i == 0 else ""}><span>{icon(s["icon"])}{s["name"]}</span></label>'
        for i, s in enumerate(SERVICES))
    svc_opts += f'<label class="opt"><input type="radio" name="service" value="Something else" data-key="other"><span>{icon("dots")}Something else</span></label>'
    drops = ''.join(f'''<label class="drop"><input type="file" name="photo{i}" accept="image/*" aria-label="Photo {i}"><span class="drop-ui">{icon('camera')}Add photo</span><span class="drop-name"></span></label>''' for i in (1, 2, 3))
    main = f'''<section class="page-hero" style="padding-bottom:clamp(32px,4vw,48px)">
  <div class="container page-hero-copy">
    {crumbs(trail)}
    <span class="eyebrow">Free quote</span>
    <h1 class="h1" data-split>Let's clear it out.</h1>
    <p class="lead" data-reveal>Tell us what needs to go and add a few photos. We'll get back to you with a clear, upfront price — free, with no obligation.</p>
  </div>
</section>
<section class="section" style="padding-top:0">
  <div class="container quote-layout">
    <div class="quote-card" data-reveal>
      <form id="quote-form" name="quote" method="POST" action="https://formsubmit.co/{SITE['email']}" enctype="multipart/form-data">
        <input type="hidden" name="_subject" value="New quote request from the website">
        <input type="hidden" name="_template" value="table">
        <input type="hidden" name="_captcha" value="false">
        <input type="hidden" name="_next" value="{SITE['url']}/thanks/">
        <p class="hp" aria-hidden="true"><label>Leave blank <input name="_honey" tabindex="-1" autocomplete="off"></label></p>
        <div class="qf-top js-only" style="display:grid">
          <div class="qf-meta"><span class="qf-count" aria-live="polite">Step 1 of 3</span><span class="qf-title muted">What needs to go?</span></div>
          <div class="qf-progress"><span></span></div>
        </div>

        <fieldset class="qf-step is-active" data-title="What needs to go?">
          <legend>What can we help with?</legend>
          <div class="field">
            <div class="opts opts--2" role="radiogroup" aria-label="Service">{svc_opts}</div>
            <p class="field-error">Please choose a service.</p>
          </div>
          <div class="field">
            <label for="details">What's going? <span class="opt-label">(optional)</span></label>
            <textarea class="input" id="details" name="details" placeholder="e.g. old couch, two mattresses, and a garage full of boxes"></textarea>
          </div>
          <div class="field">
            <span class="label">Photos <span class="opt-label">(optional, up to 3)</span></span>
            <div class="drops">{drops}</div>
            <span class="hint">Photos help us give you an accurate price, fast.</span>
          </div>
          <div class="qf-nav js-only"><button class="btn btn-primary" type="button" data-next>Next{icon('arrow', 'ic-arrow')}</button></div>
        </fieldset>

        <fieldset class="qf-step" data-title="Where & when">
          <legend>Where and when?</legend>
          <div class="field">
            <label for="address">Address or ZIP code</label>
            <input class="input" id="address" name="address" autocomplete="street-address" required>
            <p class="field-error">Please add an address or ZIP so we know where to go.</p>
          </div>
          <div class="field">
            <label for="timing">When would you like it gone?</label>
            <select class="input" id="timing" name="timing">
              <option>As soon as possible</option><option>This week</option><option>In the next 2 weeks</option><option>I'm flexible</option>
            </select>
          </div>
          <div class="qf-nav js-only"><button class="btn btn-ghost" type="button" data-prev>{icon('arrow-left')}Back</button><button class="btn btn-primary" type="button" data-next>Next{icon('arrow', 'ic-arrow')}</button></div>
        </fieldset>

        <fieldset class="qf-step" data-title="Your details">
          <legend>How do we reach you?</legend>
          <div class="field">
            <label for="name">Your name</label>
            <input class="input" id="name" name="name" autocomplete="name" required>
            <p class="field-error">Please add your name.</p>
          </div>
          <div class="row-2">
            <div class="field">
              <label for="phone">Phone</label>
              <input class="input" id="phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" required>
              <p class="field-error">Please add a phone number.</p>
            </div>
            <div class="field">
              <label for="email">Email <span class="opt-label">(optional)</span></label>
              <input class="input" id="email" name="email" type="email" autocomplete="email">
              <p class="field-error">That email doesn't look quite right.</p>
            </div>
          </div>
          <div class="field">
            <span class="label">Best way to reach you</span>
            <div class="opts opts--3" role="radiogroup" aria-label="Contact preference">
              <label class="opt"><input type="radio" name="contact_pref" value="Text" checked><span>{icon('message')}Text</span></label>
              <label class="opt"><input type="radio" name="contact_pref" value="Call"><span>{icon('phone')}Call</span></label>
              <label class="opt"><input type="radio" name="contact_pref" value="Email"><span>{icon('mail')}Email</span></label>
            </div>
          </div>
          <div class="qf-nav"><button class="btn btn-ghost js-only" type="button" data-prev>{icon('arrow-left')}Back</button><button class="btn btn-primary" type="submit"><span>Send my quote request</span>{icon('arrow', 'ic-arrow')}</button></div>
          <p class="qf-fine">Free and no obligation. We'll only use your info to reply about this job.</p>
        </fieldset>
      </form>
    </div>
    <aside class="quote-aside card" data-reveal>
      <h2 class="h3">What happens next</h2>
      <ol class="aside-list">
        <li><span class="n">1</span><p>We review your details and photos.</p></li>
        <li><span class="n">2</span><p>You get a clear, upfront price — no hidden fees.</p></li>
        <li><span class="n">3</span><p>We schedule a time that works, often the same week.</p></li>
      </ol>
      <div class="contact-lines">
        <p class="muted" style="font-size:.9rem">Rather talk? We're a call or text away.</p>
        <a href="tel:{SITE['tel']}">{icon('phone')}Call {SITE['phone']}</a>
        <a href="sms:{SITE['tel']}">{icon('message')}Text photos to {SITE['phone']}</a>
        <a href="mailto:{SITE['email']}">{icon('mail')}{SITE['email']}</a>
      </div>
    </aside>
  </div>
</section>'''
    page('contact/', 'Get a Free Junk Removal Quote | Declutter — Wichita, KS',
         'Get a free, upfront junk removal quote in Wichita, KS. Send a few photos online or call/text (316) 749-8109.',
         main, active='contact', schema=[business_schema(), crumbs_schema(trail)])


def thanks():
    main = f'''<section class="page-hero" style="min-height:70vh;display:grid;align-items:center">
  <div class="container page-hero-copy">
    <span class="eyebrow">Request received</span>
    <h1 class="h1" data-split>Thanks — we've got it.</h1>
    <p class="lead" data-reveal>We'll review your details and photos and reach out with a clear, upfront price. Need us sooner? Give us a call.</p>
    <div class="hero-actions" data-reveal><a class="btn btn-primary" href="tel:{SITE['tel']}">{icon('phone')}Call {SITE['phone']}</a><a class="btn btn-ghost" href="/">Back to home</a></div>
  </div>
</section>'''
    page('thanks/', 'Thanks! | Declutter Junk Removal', 'Your quote request was received.', main, noindex=True)


def not_found():
    main = f'''<section class="page-hero" style="min-height:70vh;display:grid;align-items:center">
  <div class="container page-hero-copy">
    <span class="eyebrow">404</span>
    <h1 class="h1">This page got hauled away.</h1>
    <p class="lead">The page you're looking for isn't here. Let's get you back on track.</p>
    <div class="hero-actions"><a class="btn btn-primary" href="/">Go home{icon('arrow', 'ic-arrow')}</a><a class="btn btn-ghost" href="/contact/">Get a free quote</a></div>
  </div>
</section>'''
    page('404.html', 'Page not found | Declutter', 'Page not found.', main, noindex=True)


# ============================================================================
# BRAND ASSETS, STATIC FILES, SEO FILES
# ============================================================================
LOGO = {'w': 0, 'h': 0}


def build_brand():
    dest = OUT / 'assets' / 'brand'
    dest.mkdir(parents=True, exist_ok=True)
    src = BRAND / 'logo-source.png'
    if not HAVE_PIL:
        shutil.copy2(src, dest / 'logo.png')
        LOGO.update(w=280, h=100)
        return
    im = Image.open(src).convert('RGBA')
    im = im.crop(im.getbbox())
    w = 560
    logo = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    logo.save(dest / 'logo.png', optimize=True)
    LOGO.update(w=logo.width, h=logo.height)

    # Favicon from the leaf
    px = im.load()
    xs, ys = [], []
    for y in range(0, im.height, 2):
        for x in range(0, im.width, 2):
            r, g, b, a = px[x, y]
            if a > 200 and g > 150 and r < 150:
                xs.append(x); ys.append(y)
    leaf = im.crop((min(xs), min(ys), max(xs) + 2, max(ys) + 2))
    for size, name in ((512, 'icon-512.png'), (180, 'apple-touch-icon.png'), (32, 'favicon-32.png')):
        canvas = Image.new('RGBA', (size, size), (11, 14, 12, 255))
        l = leaf.copy()
        l.thumbnail((int(size * .7), int(size * .7)), Image.LANCZOS)
        canvas.alpha_composite(l, ((size - l.width) // 2, (size - l.height) // 2))
        canvas.convert('RGB').save(dest / name)

    # Social share image
    og = Image.new('RGB', (1200, 630), (11, 14, 12))
    bg = find_photo('before-after/two-car-garage-after')
    if bg:
        p = ImageOps.exif_transpose(Image.open(bg)).convert('RGB')
        p = ImageOps.fit(p, (1200, 630), Image.LANCZOS, centering=(.5, .45))
        og = Image.blend(p, Image.new('RGB', (1200, 630), (11, 14, 12)), .72)
    l = im.copy()
    l.thumbnail((760, 300), Image.LANCZOS)
    og = og.convert('RGBA')
    og.alpha_composite(l, ((1200 - l.width) // 2, (630 - l.height) // 2))
    og.convert('RGB').save(dest / 'og.jpg', quality=86)


def copy_static():
    for sub in ('css', 'js'):
        d = OUT / 'assets' / sub
        d.mkdir(parents=True, exist_ok=True)
        for f in (STATIC / sub).iterdir():
            shutil.copy2(f, d / f.name)
    ASSET_V['css'] = hashlib.md5((STATIC / 'css' / 'styles.css').read_bytes()).hexdigest()[:8]
    ASSET_V['js'] = hashlib.md5((STATIC / 'js' / 'main.js').read_bytes()).hexdigest()[:8]
    vid = PHOTOS / 'video'
    if vid.exists():
        (OUT / 'assets' / 'video').mkdir(parents=True, exist_ok=True)
        for f in vid.glob('*.mp4'):
            shutil.copy2(f, OUT / 'assets' / 'video' / f.name)


def seo_files():
    today = date.today().isoformat()
    urls = ''.join(f'<url><loc>{u}</loc><lastmod>{today}</lastmod></url>' for u in PAGES)
    (OUT / 'sitemap.xml').write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {SITE["url"]}/sitemap.xml\n')


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    copy_static()
    build_brand()
    home()
    services_index()
    for s in SERVICES:
        service_page(s)
    areas_index()
    for a in AREAS:
        area_page(a)
    about()
    contact()
    thanks()
    not_found()
    seo_files()
    missing = [n for n in ('service-garage', 'service-junk', 'service-hot-tub', 'crew-member', 'crew-vests') if not find_photo(n)]
    print(f'Built {len(PAGES)} indexable pages into {OUT}')
    if not HAVE_PIL:
        print('Note: Pillow not installed — photos copied without resizing. Run: pip3 install Pillow')
    if missing:
        print('Missing photos:', ', '.join(missing))


if __name__ == '__main__':
    main()
