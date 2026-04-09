"""Migrate Korean addresses to database"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.connection import init_database
from database.repository import KoreanAddressRepository
from utils.logger import log


# 100 Korean addresses
ADDRESSES = [
    ("1, Jong-ro", "Kyobo Building", "Seoul", "03154", "Seoul"),
    ("128, Yeoui-daero", "LG Twin Towers", "Seoul", "07336", "Seoul"),
    ("26, Jong-ro", "SK Building", "Seoul", "03188", "Seoul"),
    ("330, Dongho-ro", "CJ CheilJedang Center", "Seoul", "04560", "Seoul"),
    ("12, Heolleung-ro", "Hyundai Motor Building", "Seoul", "06763", "Seoul"),
    ("33, Jong-ro 3-gil", "KT Gwanghwamun Building", "Seoul", "03155", "Seoul"),
    ("20, Sejong-daero 9-gil", "Shinhan Bank Building", "Seoul", "04513", "Seoul"),
    ("508, Nonhyeon-ro", "GS Tower", "Seoul", "06141", "Seoul"),
    ("3, Huiujeong-ro 1-gil", "YG Entertainment", "Seoul", "04028", "Seoul"),
    ("205, Gangdong-daero", "JYP Center", "Seoul", "05407", "Seoul"),
    ("83-21, Wangsimni-ro", "SM Entertainment", "Seoul", "04769", "Seoul"),
    ("570, Songpa-daero", "Coupang Tower 730", "Seoul", "05510", "Seoul"),
    ("42, Hangang-daero", "HYBE Yongsan", "Seoul", "04389", "Seoul"),
    ("65, Eulji-ro", "SK T-Tower", "Seoul", "04539", "Seoul"),
    ("100, Hangang-daero", "Amorepacific HQ", "Seoul", "04386", "Seoul"),
    ("1, Gwanak-ro", "Seoul National University", "Seoul", "08826", "Seoul"),
    ("50, Yonsei-ro", "Yonsei University", "Seoul", "03722", "Seoul"),
    ("145, Anam-ro", "Korea University", "Seoul", "02841", "Seoul"),
    ("30, Munjeon-ro", "BNK Busan Bank", "Busan", "48400", "Busan"),
    ("166, Pangyoyeok-ro", "Kakao Agit", "Seongnam-si", "13529", "Gyeonggi-do"),
    ("117, Bundangnaeryuk-ro", "LINE Square", "Seongnam-si", "13591", "Gyeonggi-do"),
    ("6, Buljeong-ro", "Naver Green Factory", "Seongnam-si", "13561", "Gyeonggi-do"),
    ("477, Bundang-suseo-ro", "HD Hyundai GRC", "Seongnam-si", "13591", "Gyeonggi-do"),
    ("300, Olympic-ro", "Lotte World Tower", "Seoul", "05551", "Seoul"),
    ("11, Yeouido-ro", "FKI Tower", "Seoul", "07320", "Seoul"),
    ("10, Gukjegeumyung-ro", "IFC Seoul", "Seoul", "07326", "Seoul"),
    ("24, Yeoui-daero", "FKI Tower", "Seoul", "07320", "Seoul"),
    ("513, Yeongdong-daero", "COEX Convention Center", "Seoul", "06164", "Seoul"),
    ("624, Gangnam-daero", "ICT Tower", "Seoul", "06060", "Seoul"),
    ("416, Maetan-dong", "Samsung Electronics", "Suwon-si", "16677", "Gyeonggi-do"),
    ("209, Neungdong-ro", "Konkuk University", "Seoul", "05029", "Seoul"),
    ("222, Wangsimni-ro", "Hanyang University", "Seoul", "04763", "Seoul"),
    ("52, Ewhayeodae-gil", "Ewha Womans University", "Seoul", "03760", "Seoul"),
    ("77, Deogyeong-daero", "Kyung Hee University", "Yongin-si", "17104", "Gyeonggi-do"),
    ("100, Cheonggyesan-ro", "E-Mart HQ", "Seoul", "04637", "Seoul"),
    ("7, Teheran-ro 78-gil", "POSCO Center", "Seoul", "06194", "Seoul"),
    ("231, Teheran-ro", "Centerfield West", "Seoul", "06142", "Seoul"),
    ("131, Ttukseom-ro", "Musinsa HQ", "Seoul", "04782", "Seoul"),
    ("25, Gukjegeumyung-ro 2-gil", "Shinhan Investment", "Seoul", "07327", "Seoul"),
    ("33, Gukjegeumyung-ro 8-gil", "NH Investment", "Seoul", "07335", "Seoul"),
    ("123, Lotte-ro", "Lotte Shopping HQ", "Seoul", "05551", "Seoul"),
    ("129, Samsung-ro", "Samsung SDS", "Seoul", "05510", "Seoul"),
    ("735, Teheran-ro", "Hanwha Life", "Seoul", "06133", "Seoul"),
    ("98, Huam-ro", "LG CNS", "Seoul", "04637", "Seoul"),
    ("21, Baekbeom-ro", "Sogang University", "Seoul", "04107", "Seoul"),
    ("206, World Cup-ro", "Seoul World Cup Stadium", "Seoul", "03929", "Seoul"),
    ("40, Cheonggyecheon-ro", "KTO Seoul Office", "Seoul", "04521", "Seoul"),
    ("110, Sejong-daero", "Seoul City Hall", "Seoul", "04524", "Seoul"),
    ("1, Cheongwadae-ro", "The Blue House", "Seoul", "03048", "Seoul"),
    ("161, Sajik-ro", "Gyeongbokgung Palace", "Seoul", "03045", "Seoul"),
    ("11, Gwangnaru-ro 56-gil", "Techno Mart", "Seoul", "05048", "Seoul"),
    ("40, Pyeongtaekhang-ro", "Samsung Pyeongtaek", "Pyeongtaek-si", "17786", "Gyeonggi-do"),
    ("272, Jungang-daero", "Busan Railway Station", "Busan", "48733", "Busan"),
    ("77, Centum jungang-ro", "Busan Centum City", "Busan", "48058", "Busan"),
    ("30, Centum seo-ro", "KNN Tower", "Busan", "48058", "Busan"),
    ("210, Marine city 2-ro", "Haeundae I-Park", "Busan", "48093", "Busan"),
    ("45, Somang-ro", "Incheon Int Airport", "Incheon", "22382", "Incheon"),
    ("165, Convensia-daero", "NEATT Tower", "Incheon", "21998", "Incheon"),
    ("204, Convensia-daero", "Incheon Songdo Central Park", "Incheon", "21995", "Incheon"),
    ("119, Michuhol-daero", "Incheon City Hall", "Incheon", "21554", "Incheon"),
    ("80, Daehak-ro", "KAIST Main Campus", "Daejeon", "34141", "Daejeon"),
    ("100, Dunsan-ro", "Daejeon City Hall", "Daejeon", "35242", "Daejeon"),
    ("1, Gonsin-ro", "Daegu City Hall", "Daegu", "41911", "Daegu"),
    ("20, Sincheon-dong", "Daegu Shinsegae", "Daegu", "41223", "Daegu"),
    ("88, World cup-ro", "Daegu Stadium", "Daegu", "42250", "Daegu"),
    ("120, Juyeop-ro", "KINTEX Exhibition", "Goyang-si", "10390", "Gyeonggi-do"),
    ("10, Chungmin-ro", "Garden 5", "Seoul", "05836", "Seoul"),
    ("20, Sejong-ro", "Gwanghwamun Square", "Seoul", "03154", "Seoul"),
    ("30, Insa-dong gil", "Insa-dong Center", "Seoul", "03148", "Seoul"),
    ("21, Dosan-daero 45-gil", "Horim Museum", "Seoul", "06020", "Seoul"),
    ("15, Toegye-ro", "Namdaemun Market", "Seoul", "04529", "Seoul"),
    ("21, Myeongdong-gil", "Myeongdong Theater", "Seoul", "04534", "Seoul"),
    ("105, Namsangongwon-gil", "N Seoul Tower", "Seoul", "04340", "Seoul"),
    ("281, Eulji-ro", "Dongdaemun Design Plaza", "Seoul", "04551", "Seoul"),
    ("113, Hangan-daero", "Yongsan Station", "Seoul", "04377", "Seoul"),
    ("16, Itaewon-ro", "War Memorial of Korea", "Seoul", "04353", "Seoul"),
    ("176, Sinchon-ro", "Sinchon Station", "Seoul", "04104", "Seoul"),
    ("160, Yanghwa-ro", "Hongdae Station", "Seoul", "04050", "Seoul"),
    ("1, World cup buk-ro", "Digital Media City", "Seoul", "03925", "Seoul"),
    ("30, Bamgogae-ro 1-gil", "Suseo Station", "Seoul", "06349", "Seoul"),
    ("6, Teheran-ro 52-gil", "Shinsegae Food", "Seoul", "06212", "Seoul"),
    ("12, Bongeunsa-ro 108-gil", "InterContinental Seoul", "Seoul", "06170", "Seoul"),
    ("434, Gangnam-daero", "Gangnam Kyobo", "Seoul", "06129", "Seoul"),
    ("152, Teheran-ro", "Gangnam Finance Center", "Seoul", "06236", "Seoul"),
    ("179, Sejong-daero", "Sejong Center", "Seoul", "03172", "Seoul"),
    ("222, Banpo-daero", "Seoul Catholic Univ Hospital", "Seoul", "06591", "Seoul"),
    ("55, Sejong-daero", "Bank of Korea", "Seoul", "04531", "Seoul"),
    ("35, Namdaemun-ro 7-gil", "Lotte Hotel Seoul", "Seoul", "04533", "Seoul"),
    ("124, Sogong-ro", "Westin Josun Seoul", "Seoul", "04526", "Seoul"),
    ("19, Uisadang-daero", "National Assembly", "Seoul", "07233", "Seoul"),
    ("21, Maeyeong-ro", "Samsung Digital City", "Suwon-si", "16677", "Gyeonggi-do"),
    ("70, Dongtan-gil", "Samsung Hwaseong Campus", "Hwaseong-si", "18448", "Gyeonggi-do"),
    ("200, Gyeongje-ro", "Gwanggyo Business Center", "Suwon-si", "16503", "Gyeonggi-do"),
    ("1, Pangyoyeok-ro 146-gil", "Pangyo Techno Valley", "Seongnam-si", "13487", "Gyeonggi-do"),
    ("25, Gasan digital 1-ro", "Gasan Digital Center", "Seoul", "08501", "Seoul"),
    ("12, Digital-ro 31-gil", "Guro Digital Tower", "Seoul", "08380", "Seoul"),
    ("242, Cheongsa-ro", "Government Complex Daejeon", "Daejeon", "35208", "Daejeon"),
    ("20, Heolleung-ro", "KOTRA HQ", "Seoul", "06792", "Seoul"),
    ("46, Ttukseom-ro 1-gil", "Seoul Forest Park", "Seoul", "04766", "Seoul"),
    ("136, Gye-dong gil", "Bukchon Hanok Village", "Seoul", "03056", "Seoul"),
]


def main():
    """Migrate addresses to database"""
    log.info("=" * 60)
    log.info("🏢 MIGRATING KOREAN ADDRESSES TO DATABASE")
    log.info("=" * 60)
    
    # Initialize database
    init_database()
    
    # Add addresses
    success_count = 0
    skip_count = 0
    
    for line1, line2, city, postal_code, state in ADDRESSES:
        try:
            result = KoreanAddressRepository.create(
                line1=line1,
                line2=line2,
                city=city,
                postal_code=postal_code,
                state=state
            )
            
            if result:
                success_count += 1
            else:
                skip_count += 1
                
        except Exception as e:
            log.error(f"❌ Failed to add address: {line1} - {e}")
            skip_count += 1
    
    log.info("")
    log.info("=" * 60)
    log.success(f"✅ Migration completed!")
    log.info(f"   Added: {success_count}")
    log.info(f"   Skipped: {skip_count}")
    log.info(f"   Total: {len(ADDRESSES)}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
