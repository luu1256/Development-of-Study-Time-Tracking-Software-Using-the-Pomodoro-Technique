<?php

use App\Http\Controllers\Catalog\WishlistController;
use Illuminate\Support\Facades\Route;

Route::middleware(['auth', 'role:buyer'])->group(function () {
    Route::get('/wishlist', [WishlistController::class, 'index'])->name('wishlist.index');
    Route::post('/wishlist/{product}/toggle', [WishlistController::class, 'toggle'])->name('wishlist.toggle');
});
