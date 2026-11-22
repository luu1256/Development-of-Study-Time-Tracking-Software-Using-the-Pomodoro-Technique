<?php

namespace App\Http\Controllers\Catalog;

use App\Http\Controllers\Controller;
use App\Models\Category;
use App\Models\Product;
use App\Models\Shop;
use Illuminate\Support\Facades\Auth;
use Illuminate\View\View;

class HomeController extends Controller
{
    public function index(): View
    {
        $categories = Category::orderBy('name')->get();

        $featuredProducts = Product::public()
            ->with(['category', 'shop'])
            ->latest()
            ->take(8)
            ->get();

        $featuredShops = Shop::where('status', 'approved')
            ->withCount(['products' => function ($query) {
                $query->public();
            }])
            ->latest()
            ->take(4)
            ->get();

        $wishlistIds = Auth::check()
            ? Auth::user()->wishlistProducts()->pluck('products.id')->toArray()
            : [];

        return view('catalog.home', compact(
            'categories',
            'featuredProducts',
            'featuredShops',
            'wishlistIds'
        ));
    }
}
