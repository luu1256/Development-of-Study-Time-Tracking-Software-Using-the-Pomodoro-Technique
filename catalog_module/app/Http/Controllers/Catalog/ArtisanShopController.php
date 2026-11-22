<?php

namespace App\Http\Controllers\Catalog;

use App\Http\Controllers\Controller;
use App\Models\Product;
use App\Models\Shop;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\View\View;

class ArtisanShopController extends Controller
{
    public function show(Request $request, Shop $shop): View
    {
        abort_unless($shop->status === 'approved', 404);

        $shop->load('user');

        $query = Product::public()
            ->with('category')
            ->where('shop_id', $shop->id);

        switch ($request->input('sort')) {
            case 'price_asc':
                $query->orderBy('price', 'asc');
                break;
            case 'price_desc':
                $query->orderBy('price', 'desc');
                break;
            default:
                $query->latest();
                break;
        }

        $products = $query->paginate(8)->withQueryString();
        $totalProducts = Product::public()->where('shop_id', $shop->id)->count();

        $wishlistIds = Auth::check()
            ? Auth::user()->wishlistProducts()->pluck('products.id')->toArray()
            : [];

        return view('catalog.shop_detail', compact(
            'shop',
            'products',
            'totalProducts',
            'wishlistIds'
        ));
    }
}
