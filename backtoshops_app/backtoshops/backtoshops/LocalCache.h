//
//  LocalCache.h
//  Scholacloud
//
//  Created by Ding Nicholas on 11/17/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface LocalCache : NSObject {
    NSMutableDictionary *keyStore;
}

+ (LocalCache *)sharedLocalCache;

- (void)storeKey:(NSString *)key;
- (BOOL)hasKey:(NSString *)key;

- (void)storeArray:(NSArray *)array forKey:(NSString *)key;
- (NSArray *)cachedArrayWithKey:(NSString *)key;
- (void)storeDictionary:(NSDictionary *)dictionary forKey:(NSString *)key;
- (NSDictionary *)cachedDictionaryWithKey:(NSString *)key;

- (void)invalidate;

@end
