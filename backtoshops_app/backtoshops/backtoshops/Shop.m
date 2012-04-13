//
//  Shop.m
//  backtoshops
//
//  Created by Ding Nicholas on 2/16/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "Shop.h"

@implementation Shop

@synthesize identifier, name, imageURL, location;
@synthesize upc, hours;
@synthesize coordinate;

- (void)dealloc
{
    [identifier release];
    [name release];
    [imageURL release];
    [upc release];
    [hours release];
    [location release];
    [super dealloc];
}

- (NSString *)toJSON
{
    NSString *jsonText = [NSString stringWithFormat:@"{'id': '%@', 'name': '%@', 'imageURL': '%@', 'location': \"%@\"}",
                          identifier, name, imageURL, location];
    return jsonText;
}

+ (id)shopFromXML:(GDataXMLElement *)el
{
    Shop *shopObj = [[[Shop alloc] init] autorelease];
    shopObj.identifier = [[el attributeForName:@"id"] stringValue];
    shopObj.name = [[[el elementsForName:@"name"] lastObject] stringValue];
    shopObj.location = [NSString stringWithFormat:@"%@<br/>%@ %@", 
                        [[[el elementsForName:@"addr"] lastObject] stringValue], 
                        [[[el elementsForName:@"zip"] lastObject] stringValue], 
                        [[[el elementsForName:@"city"] lastObject] stringValue]];
    shopObj.upc = [[[el elementsForName:@"upc"] lastObject] stringValue];
    shopObj.imageURL = [[[el elementsForName:@"img"] lastObject] stringValue];
    shopObj.hours = [[[el elementsForName:@"hours"] lastObject] stringValue];
    double lat = [[[[[el elementsForName:@"location"] lastObject] attributeForName:@"lat"] stringValue] doubleValue];
    double lng = [[[[[el elementsForName:@"location"] lastObject] attributeForName:@"long"] stringValue] doubleValue];
    shopObj.coordinate = CLLocationCoordinate2DMake(lat, lng);
    return shopObj;
}

- (id)initWithCoder:(NSCoder *)aDecoder
{
    self = [super init];
    if (self) {
        self.identifier = [aDecoder decodeObjectForKey:@"identifier"];
        self.name = [aDecoder decodeObjectForKey:@"name"];
        self.location = [aDecoder decodeObjectForKey:@"location"];
        self.imageURL = [aDecoder decodeObjectForKey:@"imageURL"];
        self.upc = [aDecoder decodeObjectForKey:@"upc"];
        self.hours = [aDecoder decodeObjectForKey:@"hours"];
        double latitude = [aDecoder decodeDoubleForKey:@"coordinate.latitude"];
        double longitude = [aDecoder decodeDoubleForKey:@"coordinate.longitude"];
        self.coordinate = CLLocationCoordinate2DMake(latitude, longitude);
    }
    return self;
}

- (void)encodeWithCoder:(NSCoder *)aCoder
{    
    [aCoder encodeObject:self.identifier forKey:@"identifier"];
    [aCoder encodeObject:self.name forKey:@"name"];
    [aCoder encodeObject:self.location forKey:@"location"];
    [aCoder encodeObject:self.imageURL forKey:@"imageURL"];
    [aCoder encodeObject:self.upc forKey:@"upc"];
    [aCoder encodeObject:self.hours forKey:@"hours"];
    [aCoder encodeDouble:self.coordinate.latitude forKey:@"coordinate.latitude"];
    [aCoder encodeDouble:self.coordinate.longitude forKey:@"coordinate.longitude"];
}

@end
