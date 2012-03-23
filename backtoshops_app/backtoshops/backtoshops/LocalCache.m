//
//  LocalCache.m
//  Scholacloud
//
//  Created by Ding Nicholas on 11/17/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import "LocalCache.h"

@interface LocalCache (Private)

- (NSMutableDictionary *)loadKeyStore;

@end
    
@implementation LocalCache

+ (LocalCache *)sharedLocalCache
{
    static LocalCache *instance = NULL;
    
    @synchronized(self) {
        if (!instance) {
            instance = [[LocalCache alloc] init];
        }
        
        return instance;
    }
}

- (void)dealloc
{
    [keyStore release];
    [super dealloc];
}

- (NSMutableDictionary *)loadKeyStore
{
    NSFileManager *fileManager = [NSFileManager defaultManager];
    NSString *cacheDir = [NSSearchPathForDirectoriesInDomains(NSCachesDirectory, NSUserDomainMask, YES) lastObject];
    NSString *filePath = [NSString stringWithFormat:@"%@/SimpleKeyStore.plist", cacheDir];
    
    if ([fileManager fileExistsAtPath:filePath]) {
        return [[[NSMutableDictionary alloc] initWithContentsOfFile:filePath] autorelease];
    } else {
        return [[[NSMutableDictionary alloc] init] autorelease];
    }
}

- (id)init
{
    self = [super init];
    if (self) {
        NSFileManager *fileManager = [NSFileManager defaultManager];
        NSString *cacheDir = [NSSearchPathForDirectoriesInDomains(NSCachesDirectory, NSUserDomainMask, YES) lastObject];
        NSString *filePath = [NSString stringWithFormat:@"%@/SimpleKeyStore.plist", cacheDir];
        
        if ([fileManager fileExistsAtPath:filePath]) {
            keyStore = [[NSMutableDictionary alloc] initWithContentsOfFile:filePath];
        } else {
            keyStore = [[NSMutableDictionary alloc] init];
        }
    }
    return self;
}

- (void)storeKey:(NSString *)key
{
    NSString *cacheDir = [NSSearchPathForDirectoriesInDomains(NSCachesDirectory, NSUserDomainMask, YES) lastObject];
    NSString *filePath = [NSString stringWithFormat:@"%@/SimpleKeyStore.plist", cacheDir];
    [keyStore setValue:@"#" forKey:key];
    BOOL res = [keyStore writeToFile:filePath atomically:YES];
    
    if (res == false) {
        NSLog(@"[LocalCache] Failed to store key %@", key);
    } else {
        NSLog(@"[LocalCache] Store key %@ in %@", key, filePath);
    }    
}

- (BOOL)hasKey:(NSString *)key
{
    if ([keyStore valueForKey:key] != nil)
        return YES;
    return NO;
}

- (void)storeArray:(NSArray *)array forKey:(NSString *)key
{
    NSString *cacheDir = [NSSearchPathForDirectoriesInDomains(NSCachesDirectory, NSUserDomainMask, YES) lastObject];
    NSString *filePath = [NSString stringWithFormat:@"%@/%@.plist", cacheDir, key];
    BOOL res = [array writeToFile:filePath atomically:YES];
    
    if (res == NO) {
        NSLog(@"[LocalCache] Failed to store array[%d] in %@", [array count], filePath);
    } else {
        NSLog(@"[LocalCache] Store array[%d] in %@", [array count], filePath);
    }
}

- (NSArray *)cachedArrayWithKey:(NSString *)key
{
    NSFileManager *fileManager = [NSFileManager defaultManager];
    NSString *cacheDir = [NSSearchPathForDirectoriesInDomains(NSCachesDirectory, NSUserDomainMask, YES) lastObject];
    NSString *filePath = [NSString stringWithFormat:@"%@/%@.plist", cacheDir, key];
    
    if ([fileManager fileExistsAtPath:filePath]) {
        NSLog(@"[LocalCache] Retrieve cached array from %@", filePath);
        return [NSArray arrayWithContentsOfFile:filePath];
    }
    
    NSLog(@"[LocalCache] Retrieve cahced array from %@ was failed", filePath);
    return nil;
}

- (void)storeDictionary:(NSDictionary *)dictionary forKey:(NSString *)key
{
    NSString *cacheDir = [NSSearchPathForDirectoriesInDomains(NSCachesDirectory, NSUserDomainMask, YES) lastObject];
    NSString *filePath = [NSString stringWithFormat:@"%@/%@.plist", cacheDir, key];
    
    NSData * myData = [NSKeyedArchiver archivedDataWithRootObject:dictionary];
    BOOL res = [myData writeToFile:filePath atomically:YES];
    
    if (res == NO) {
        NSLog(@"[LocalCache] Failed to store dictionary[%d] in %@", [dictionary count], filePath);
    } else {
        NSLog(@"[LocalCache] Store dictionary[%d] in %@", [dictionary count], filePath);
    }
}

- (NSDictionary *)cachedDictionaryWithKey:(NSString *)key
{
    NSFileManager *fileManager = [NSFileManager defaultManager];
    NSString *cacheDir = [NSSearchPathForDirectoriesInDomains(NSCachesDirectory, NSUserDomainMask, YES) lastObject];
    NSString *filePath = [NSString stringWithFormat:@"%@/%@.plist", cacheDir, key];
    
    if ([fileManager fileExistsAtPath:filePath]) {
        NSLog(@"[LocalCache] Retrieve cached dictionary from %@", filePath);
        NSData * myData = [NSData dataWithContentsOfFile:filePath];
        NSDictionary * myDict = [NSKeyedUnarchiver unarchiveObjectWithData:myData];
        return myDict;
    }
    
    NSLog(@"[LocalCache] Retrieve cahced dictionary from %@ was failed", filePath);
    return nil;
}


- (void)invalidate
{
    NSFileManager *fileManager = [NSFileManager defaultManager];
    NSString *cacheDir = [NSSearchPathForDirectoriesInDomains(NSCachesDirectory, NSUserDomainMask, YES) lastObject];
    NSArray *fileList = [fileManager contentsOfDirectoryAtPath:cacheDir error:NULL];
    
    for (NSString *key in fileList) {
        if ([key hasSuffix:@"plist"]) {;
            NSLog(@"[LocalCache] Invalidate cache %@", [NSString stringWithFormat:@"%@/%@", cacheDir, key]);
            [fileManager removeItemAtPath:[NSString stringWithFormat:@"%@/%@", cacheDir, key] error:NULL];
        }
    }
    
    [fileManager release];
    
    // Re-init keyStore
    [keyStore release];
    keyStore = [[NSMutableDictionary alloc] init];
}

@end
